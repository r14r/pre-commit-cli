package main

import (
    "os"
    "path/filepath"
    "strings"
    "testing"
)

func TestDetectGo(t *testing.T) {
    root := t.TempDir()
    if err := os.WriteFile(filepath.Join(root, "go.mod"), []byte("module example.org/test\n"), 0600); err != nil { t.Fatal(err) }
    found := strings.Join(detected(root), ",")
    if !strings.Contains(found, "go") { t.Fatalf("Go detection missing: %s", found) }
}

func TestAddEnvironmentIdempotent(t *testing.T) {
    root := t.TempDir()
    for i := 0; i < 2; i++ {
        if err := add(root, []string{"base", "go"}, false); err != nil { t.Fatal(err) }
    }
    content, err := os.ReadFile(filepath.Join(root, ".pre-commit-config.yaml"))
    if err != nil { t.Fatal(err) }
    if count := strings.Count(string(content), "id: go-vet"); count != 1 { t.Fatalf("go-vet duplicated %d times", count) }
}

func TestDryRunDoesNotWrite(t *testing.T) {
    root := t.TempDir()
    if err := add(root, []string{"go"}, true); err != nil { t.Fatal(err) }
    if exists(filepath.Join(root, ".pre-commit-config.yaml")) { t.Fatal("dry-run created a file") }
}
