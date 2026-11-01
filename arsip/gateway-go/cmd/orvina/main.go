// Orvina gateway — P0 hello stack.
// Serves web/dist, /api/health, /ws/echo (WebSocket) and supervises the Python engine.
package main

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/coder/websocket"
)

const version = "0.1.0-p0"

type config struct {
	Port          string
	DataDir       string
	AppSecretKey  string
	ModelscopeTok string
	EngineURL     string
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func loadDotEnv(path string) {
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || !strings.Contains(line, "=") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		k, v := strings.TrimSpace(parts[0]), strings.Trim(strings.TrimSpace(parts[1]), `"'`)
		if _, exists := os.LookupEnv(k); !exists {
			os.Setenv(k, v)
		}
	}
}

type healthReport struct {
	Gateway    string `json:"gateway"`
	Engine     string `json:"engine"`
	Modelscope string `json:"modelscope"`
	Whisper    string `json:"whisper"`
	Version    string `json:"version"`
}

// engineSupervisor starts uvicorn as a child process and polls its health.
type engineSupervisor struct {
	mu     sync.Mutex
	url    string
	key    string
	status string // starting | ok | down
	report map[string]string
	cmd     *exec.Cmd
	dataDir string
	token   string
	stop    chan struct{}
	done    chan struct{}
}

func newEngineSupervisor(url, key, dataDir, token string) *engineSupervisor {
	return &engineSupervisor{url: url, key: key, dataDir: dataDir, token: token, status: "starting", stop: make(chan struct{}), done: make(chan struct{})}
}

func (s *engineSupervisor) start() {
	python := os.Getenv("PYTHON_BIN")
	if python == "" {
		python = "python3"
	}
	engineDir := os.Getenv("ENGINE_DIR")
	if engineDir == "" {
		engineDir = filepath.Join("..", "engine") // local dev: run from gateway/
	}
	absEngine, _ := filepath.Abs(engineDir)
	cmd := exec.Command(python, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001", "--workers", "1")
	cmd.Dir = absEngine
	cmd.Env = append(os.Environ(),
		"X_ENGINE_KEY="+s.key,
		"MODELSCOPE_TOKEN="+s.token,
		"DATA_DIR="+s.dataDir,
	)
	cmd.Stdout = logWriter("engine.out")
	cmd.Stderr = logWriter("engine.err")
	s.mu.Lock()
	s.cmd = cmd
	s.mu.Unlock()
	log.Printf("starting engine with %q in %s", python, absEngine)
	if err := cmd.Start(); err != nil {
		log.Printf("engine start failed: %v", err)
		s.setDown()
		close(s.done)
		return
	}
	go func() {
		defer close(s.done)
		tick := time.NewTicker(2 * time.Second)
		defer tick.Stop()
		for {
			select {
			case <-s.stop:
				return
			case <-tick.C:
				s.poll()
			}
		}
	}()
}

func logWriter(name string) *os.File {
	f, err := os.OpenFile(name, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return os.Stdout
	}
	return f
}

func (s *engineSupervisor) poll() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, http.MethodGet, s.url+"/v1/health", nil)
	req.Header.Set("X-Engine-Key", s.key)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		if s.status != "down" {
			log.Printf("engine unreachable: %v", err)
		}
		s.setDown()
		return
	}
	defer resp.Body.Close()
	var body map[string]any
	json.NewDecoder(resp.Body).Decode(&body)
	if resp.StatusCode != 200 {
		s.setDown()
		return
	}
	s.mu.Lock()
	s.status = "ok"
	ms, _ := body["modelscope"].(string)
	wp, _ := body["whisper"].(string)
	s.report = map[string]string{"modelscope": ms, "whisper": wp}
	s.mu.Unlock()
	log.Printf("engine healthy: modelscope=%s whisper=%s", ms, wp)
}

func (s *engineSupervisor) setDown() {
	s.mu.Lock()
	if s.status != "down" {
		log.Printf("engine is down")
	}
	s.status = "down"
	s.mu.Unlock()
}

func (s *engineSupervisor) stopProcess() {
	close(s.stop)
	s.mu.Lock()
	cmd := s.cmd
	s.mu.Unlock()
	if cmd != nil && cmd.Process != nil {
		cmd.Process.Kill()
	}
	select {
	case <-s.done:
	case <-time.After(3 * time.Second):
	}
}

func main() {
	// Local dev runs from gateway/ (so repo-root .env is ../.env). Docker runs the
	// binary from / with no .env (Studio Secrets provide the values), so also try
	// a couple of layouts for robustness.
	for _, p := range []string{".env", "../.env", "../../.env"} {
		loadDotEnv(p)
	}
	cfg := config{
		Port:          envOr("PORT", "7860"),
		DataDir:       envOr("DATA_DIR", "/tmp/orvina"),
		AppSecretKey:  os.Getenv("APP_SECRET_KEY"),
		ModelscopeTok: os.Getenv("MODELSCOPE_TOKEN"),
		EngineURL:     "http://127.0.0.1:8001",
	}
	if cfg.AppSecretKey == "" {
		log.Fatal("APP_SECRET_KEY is not set")
	}
	if err := os.MkdirAll(cfg.DataDir, 0o755); err != nil {
		log.Printf("cannot create DATA_DIR %s: %v", cfg.DataDir, err)
	}

	engineKey := deriveEngineKey(cfg.AppSecretKey)
	sup := newEngineSupervisor(cfg.EngineURL, engineKey, cfg.DataDir, cfg.ModelscopeTok)
	sup.start()
	defer sup.stopProcess()

	distFS, err := fs.Sub(loadDist(), "dist")
	if err != nil {
		log.Printf("web/dist not found (%v); serving fallback page", err)
	}

	mux := http.NewServeMux()
	cache := &healthCache{ttl: 5 * time.Minute}
	mux.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		rep := cache.get(func() healthReport {
			rep := healthReport{Gateway: "ok", Engine: sup.status, Version: version}
			sup.mu.Lock()
			if sup.status == "ok" {
				rep.Modelscope = sup.report["modelscope"]
				rep.Whisper = sup.report["whisper"]
			} else {
				rep.Modelscope = "unknown"
				rep.Whisper = "unknown"
			}
			sup.mu.Unlock()
			return rep
		})
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(rep)
	})
	mux.HandleFunc("/ws/echo", func(w http.ResponseWriter, r *http.Request) {
		conn, err := websocket.Accept(w, r, nil)
		if err != nil {
			return
		}
		defer conn.CloseNow()
		for {
			typ, msg, err := conn.Read(r.Context())
			if err != nil {
				return
			}
			if err := conn.Write(r.Context(), typ, msg); err != nil {
				return
			}
		}
	})
	if distFS != nil {
		fileServer := http.FileServer(http.FS(distFS))
		mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			p := strings.TrimPrefix(r.URL.Path, "/")
			if p != "" {
				if _, err := fs.Stat(distFS, p); err == nil {
					fileServer.ServeHTTP(w, r)
					return
				}
			}
			// SPA fallback
			r.URL.Path = "/"
			fileServer.ServeHTTP(w, r)
		})
	} else {
		mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			fmt.Fprintln(w, "<h1>Orvina gateway is running</h1><p>Build the web app first: <code>cd web && npm install && npm run build</code></p>")
		})
	}

	addr := ":" + cfg.Port
	log.Printf("gateway listening on %s", addr)
	server := &http.Server{Addr: addr, Handler: mux}
	if err := server.ListenAndServe(); err != nil {
		log.Fatal(err)
	}
}

// deriveEngineKey: HMAC-SHA256(APP_SECRET_KEY, "engine") as hex (SPEC §3.2).
func deriveEngineKey(secret string) string {
	mac := hmac.New(sha256.New, []byte(secret))
	mac.Write([]byte("engine"))
	return hex.EncodeToString(mac.Sum(nil))
}

func loadDist() fs.FS {
	candidates := []string{"../../web/dist", "../web/dist", "web/dist"}
	for _, c := range candidates {
		if st, err := os.Stat(c); err == nil && st.IsDir() {
			return os.DirFS(filepath.Dir(c))
		}
	}
	return os.DirFS(".")
}

// healthCache caches the health report for ttl (SPEC §6: cached 5 min).
type healthCache struct {
	ttl time.Duration
	mu  sync.Mutex
	at  time.Time
	val healthReport
}

func (c *healthCache) get(fn func() healthReport) healthReport {
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.val.Gateway != "" && time.Since(c.at) < c.ttl {
		return c.val
	}
	c.val = fn()
	c.at = time.Now()
	return c.val
}
