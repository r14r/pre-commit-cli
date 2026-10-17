package main

import (
 "flag"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "strings"
 "gopkg.in/yaml.v3"
)
const version="2.1.0"
type Repo struct {Repo string `yaml:"repo"`; Rev string `yaml:"rev,omitempty"`; Hooks []map[string]any `yaml:"hooks"`}
type Config struct {Repos []Repo `yaml:"repos"`}
func exists(p string) bool {_,e:=os.Stat(p);return e==nil}
func command(root string,dry bool,name string,args ...string)error {if dry {fmt.Println("DRY-RUN",name,strings.Join(args," "));return nil};c:=exec.Command(name,args...);c.Dir=root;c.Stdout=os.Stdout;c.Stderr=os.Stderr;c.Stdin=os.Stdin;return c.Run()}
func put(p string,b []byte,dry bool)error {if dry{fmt.Println("DRY-RUN write",p);return nil};if e:=os.MkdirAll(filepath.Dir(p),0755);e!=nil{return e};return os.WriteFile(p,b,0644)}
func detected(root string)[]string{out:=[]string{"base","security"};checks:=[]struct{name string;files []string}{{"go",[]string{"go.mod"}},{"python",[]string{"pyproject.toml","requirements.txt"}},{"node",[]string{"package.json"}},{"php",[]string{"composer.json"}},{"django",[]string{"manage.py"}},{"laravel",[]string{"artisan"}},{"shell",[]string{"justfile","Justfile"}},{"docker",[]string{"Dockerfile","compose.yml"}},{"markdown",[]string{"README.md"}}};for _,c:=range checks{for _,p:=range c.files{if exists(filepath.Join(root,p)){out=append(out,c.name);break}}};return out}
func hooks(ids ...string)[]map[string]any {out:=[]map[string]any{};for _,s:=range ids{out=append(out,map[string]any{"id":s})};return out}
func repos(env string)([]Repo,error){switch env{
case "base","yaml","json":return []Repo{{Repo:"https://github.com/pre-commit/pre-commit-hooks",Rev:"v5.0.0",Hooks:hooks("check-yaml","check-json","check-toml","end-of-file-fixer","trailing-whitespace")}},nil
case "security":return []Repo{{Repo:"https://github.com/pre-commit/pre-commit-hooks",Rev:"v5.0.0",Hooks:hooks("detect-private-key","check-added-large-files","check-merge-conflict")}},nil
case "gitleaks":return []Repo{{Repo:"https://github.com/gitleaks/gitleaks",Rev:"v8.28.0",Hooks:hooks("gitleaks")}},nil
case "python","django":return []Repo{{Repo:"https://github.com/astral-sh/ruff-pre-commit",Rev:"v0.8.6",Hooks:hooks("ruff","ruff-format")}},nil
case "go":return []Repo{{Repo:"local",Hooks:[]map[string]any{{"id":"go-fmt","name":"Go formatting","entry":"bash -c 'output=$(gofmt -l "$@"); test -z "$output"' --","language":"system","types":[]string{"go"}},{"id":"go-vet","name":"go vet","entry":"go vet ./...","language":"system","pass_filenames":false,"always_run":true}}}},nil
case "shell":return []Repo{{Repo:"https://github.com/scop/pre-commit-shfmt",Rev:"v3.12.0-2",Hooks:hooks("shfmt")}},nil
case "node":return []Repo{{Repo:"local",Hooks:[]map[string]any{{"id":"npm-lint","name":"npm lint","entry":"npm run lint --if-present","language":"system","pass_filenames":false}}}},nil
case "markdown":return []Repo{{Repo:"https://github.com/DavidAnson/markdownlint-cli2",Rev:"v0.44.0",Hooks:hooks("markdownlint-cli2")}},nil
case "php","laravel":return []Repo{{Repo:"local",Hooks:[]map[string]any{{"id":"composer","name":"Composer validation","entry":"composer validate --strict","language":"system","pass_filenames":false}}}},nil
case "docker":return []Repo{{Repo:"local",Hooks:[]map[string]any{{"id":"hadolint","name":"Dockerfile lint","entry":"hadolint","language":"system","files":"Dockerfile"}}}},nil
};return nil,fmt.Errorf("unknown environment %q",env)}
func add(root string,envs []string,dry bool)error{path:=filepath.Join(root,".pre-commit-config.yaml");cfg:=Config{};if b,e:=os.ReadFile(path);e==nil{if e=yaml.Unmarshal(b,&cfg);e!=nil{return e}};for _,env:=range envs{env=strings.ToLower(env);switch env{case "py":env="python";case "golang":env="go";case "js","npm","ts":env="node";case "secrets":env="gitleaks"};items,e:=repos(env);if e!=nil{return e};for _,r:=range items{idx:=-1;for i:=range cfg.Repos{if cfg.Repos[i].Repo==r.Repo{idx=i;break}};if idx<0{cfg.Repos=append(cfg.Repos,r);continue};x:=&cfg.Repos[idx];if r.Rev!=""{x.Rev=r.Rev};seen:=map[string]bool{};for _,h:=range x.Hooks{seen[fmt.Sprint(h["id"])]=true};for _,h:=range r.Hooks{if !seen[fmt.Sprint(h["id"])]{x.Hooks=append(x.Hooks,h)}}}};b,e:=yaml.Marshal(cfg);if e!=nil{return e};return put(path,b,dry)}
func precommit(root string,noInstall,dry bool)(string,error){for _,x:=range []string{".venv/bin/pre-commit",".venv/python/bin/pre-commit",".venv-pre-commit/bin/pre-commit"}{p:=filepath.Join(root,x);if exists(p){return p,nil}};if p,e:=exec.LookPath("pre-commit");e==nil{return p,nil};if noInstall{return "",fmt.Errorf("pre-commit not installed")};if e:=command(root,dry,"python3","-m","venv",".venv");e!=nil{return "",e};if e:=command(root,dry,filepath.Join(root,".venv/bin/python"),"-m","pip","install","--quiet","pre-commit");e!=nil{return "",e};return filepath.Join(root,".venv/bin/pre-commit"),nil}
func execute(root,op string,args []string,dry,noInstall bool)error{switch op{
case "version":fmt.Println("pre-commit-cli",version,"(Go)");return nil
case "list":fmt.Println("base security gitleaks shell python go node php django laravel docker markdown yaml json");return nil
case "init-git":if exists(filepath.Join(root,".git")){return nil};return command(root,dry,"git","init")
case "setup":if !exists(filepath.Join(root,".git")){if e:=command(root,dry,"git","init");e!=nil{return e}};if e:=add(root,[]string{"base","security","gitleaks"},dry);e!=nil{return e};fallthrough
case "install-hook":pc,e:=precommit(root,noInstall,dry);if e!=nil{return e};return command(root,dry,pc,"install")
case "add":if len(args)==0{return fmt.Errorf("add requires environment names")};return add(root,args,dry)
case "detect":es:=detected(root);fmt.Println("Detected:",strings.Join(es,", "));return add(root,es,dry)
case "run","autoupdate":pc,e:=precommit(root,noInstall,dry);if e!=nil{return e};if op=="autoupdate"{return command(root,dry,pc,"autoupdate")};a:=[]string{"run"};if len(args)>0{a=append(a,args[0])};return command(root,dry,pc,append(a,"--all-files")...)
case "doctor","status":fmt.Println("Project:",root,"Git:",exists(filepath.Join(root,".git")));fmt.Println("Detected:",strings.Join(detected(root),", "));fmt.Println("Precommit config:",exists(filepath.Join(root,".pre-commit-config.yaml")));if op=="doctor"{pc,e:=precommit(root,true,dry);if e!=nil{return e};return command(root,dry,pc,"validate-config")};return nil
case "fix-config","fix-gitleaks-config","fix-shfmt-config":return add(root,[]string{"base","security","shell"},dry)
case "safe-add":if e:=execute(root,"run",nil,dry,noInstall);e!=nil{return e};if len(args)>0&&args[0]=="--"{args=args[1:]};if len(args)==0{args=[]string{"."}};return command(root,dry,"git",append([]string{"add"},args...)...)
case "ci":return put(filepath.Join(root,".github/workflows/pre-commit.yml"),[]byte("name: pre-commit\non: [push, pull_request]\njobs:\n  hooks:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - run: python -m pip install -q pre-commit\n      - run: pre-commit run --all-files\n"),dry)
};return fmt.Errorf("unknown command %q",op)}
func main(){os.Exit(start())}
func start()int{fs:=flag.NewFlagSet("pre-commit-cli",flag.ContinueOnError);dir:=fs.String("dir",".","project path");dry:=fs.Bool("dry-run",false,"preview changes");no:=fs.Bool("no-install",false,"disable installation");setup:=fs.Bool("setup",false,"");detect:=fs.Bool("detect",false,"");run:=fs.Bool("run",false,"");doctor:=fs.Bool("doctor",false,"");status:=fs.Bool("status",false,"");versionFlag:=fs.Bool("version",false,"");hook:=fs.Bool("install-hook",false,"");autoupdate:=fs.Bool("autoupdate",false,"");help:=fs.Bool("help",false,"");if e:=fs.Parse(os.Args[1:]);e!=nil{return 2};op:="";args:=fs.Args();switch{case *setup:op="setup";case *detect:op="detect";case *run:op="run";case *doctor:op="doctor";case *status:op="status";case *versionFlag:op="version";case *hook:op="install-hook";case *autoupdate:op="autoupdate"};if *help||op==""&&len(args)==0{fmt.Println("pre-commit-cli Go",version,"\nCommands: setup add detect run doctor status install-hook autoupdate ci list init-git fix-config safe-add version");return 0};if op==""{op=args[0];args=args[1:]};root,e:=filepath.Abs(*dir);if e!=nil{fmt.Fprintln(os.Stderr,e);return 1};if e=execute(root,op,args,*dry,*no);e!=nil{fmt.Fprintln(os.Stderr,"ERROR:",e);return 1};return 0}
