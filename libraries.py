"""Library-aware completion data for import/include style statements."""

from __future__ import annotations

import pkgutil
import re
import sys
from functools import lru_cache

# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

PYTHON_LIBRARIES: dict[str, tuple[str, ...]] = {
    "os": (
        "path", "getcwd", "chdir", "listdir", "scandir", "mkdir", "makedirs",
        "remove", "unlink", "rename", "replace", "stat", "walk", "environ",
        "getenv", "putenv", "system", "popen", "urandom", "cpu_count", "name",
    ),
    "os.path": (
        "join", "exists", "isfile", "isdir", "islink", "isabs", "basename",
        "dirname", "splitext", "abspath", "realpath", "relpath", "normpath",
        "expanduser", "expandvars", "getsize", "getmtime", "getctime",
        "commonpath", "commonprefix",
    ),
    "sys": (
        "argv", "path", "platform", "version", "version_info", "executable",
        "stdin", "stdout", "stderr", "exit", "getsizeof", "setrecursionlimit",
        "getrecursionlimit", "modules", "maxsize", "byteorder",
    ),
    "math": (
        "pi", "e", "tau", "inf", "nan", "sqrt", "pow", "sin", "cos", "tan",
        "asin", "acos", "atan", "atan2", "log", "log10", "log2", "exp",
        "floor", "ceil", "fabs", "factorial", "gcd", "lcm", "hypot",
        "degrees", "radians", "isclose", "isfinite", "isinf", "isnan", "prod",
        "dist", "comb", "perm",
    ),
    "json": (
        "dumps", "loads", "dump", "load", "JSONDecodeError", "JSONEncoder",
        "JSONDecoder",
    ),
    "re": (
        "compile", "match", "search", "findall", "finditer", "sub", "split",
        "escape", "fullmatch", "IGNORECASE", "MULTILINE", "DOTALL", "ASCII",
        "VERBOSE", "Pattern", "Match",
    ),
    "pathlib": (
        "Path", "PurePath", "PosixPath", "WindowsPath", "PurePosixPath",
        "PureWindowsPath",
    ),
    "datetime": (
        "datetime", "date", "time", "timedelta", "timezone", "tzinfo",
        "UTC",
    ),
    "collections": (
        "defaultdict", "Counter", "deque", "OrderedDict", "namedtuple",
        "ChainMap", "UserDict", "UserList", "UserString",
    ),
    "itertools": (
        "chain", "combinations", "permutations", "product", "count", "cycle",
        "repeat", "islice", "groupby", "accumulate", "pairwise", "zip_longest",
        "tee", "takewhile", "dropwhile", "filterfalse",
    ),
    "random": (
        "random", "randint", "randrange", "choice", "choices", "shuffle",
        "sample", "seed", "uniform", "gauss", "randbytes",
    ),
    "typing": (
        "Any", "Optional", "Union", "List", "Dict", "Set", "Tuple",
        "Callable", "Iterable", "Iterator", "Sequence", "Mapping", "Protocol",
        "TypeVar", "Generic", "cast", "overload", "Literal", "TypedDict",
        "Final", "ClassVar", "NoReturn", "Never",
    ),
    "statistics": (
        "mean", "median", "mode", "stdev", "variance", "pstdev", "pvariance",
        "fmean", "geometric_mean", "harmonic_mean", "quantiles",
    ),
    "time": (
        "time", "sleep", "perf_counter", "monotonic", "strftime", "strptime",
        "localtime", "gmtime", "mktime", "time_ns",
    ),
    "subprocess": (
        "run", "Popen", "call", "check_call", "check_output", "CompletedProcess",
        "PIPE", "DEVNULL", "STDOUT", "TimeoutExpired", "CalledProcessError",
    ),
    "threading": (
        "Thread", "Lock", "RLock", "Event", "Condition", "Semaphore", "Timer",
        "Barrier", "current_thread", "active_count",
    ),
    "asyncio": (
        "run", "sleep", "gather", "create_task", "Task", "Future", "Queue",
        "Event", "Lock", "Semaphore", "wait_for", "to_thread", "StreamReader",
        "StreamWriter",
    ),
    "socket": (
        "socket", "AF_INET", "AF_INET6", "SOCK_STREAM", "SOCK_DGRAM",
        "gethostname", "gethostbyname", "create_connection",
    ),
    "sqlite3": (
        "connect", "Connection", "Cursor", "Row", "IntegrityError",
        "OperationalError",
    ),
    "argparse": (
        "ArgumentParser", "Namespace", "ArgumentError", "Action",
    ),
    "csv": (
        "reader", "writer", "DictReader", "DictWriter", "Dialect", "excel",
    ),
    "unittest": (
        "TestCase", "main", "skip", "skipIf", "expectedFailure", "mock",
    ),
    "numpy": (
        "array", "arange", "linspace", "zeros", "ones", "empty", "full",
        "eye", "random", "linalg", "mean", "median", "std", "var", "sum",
        "prod", "dot", "matmul", "reshape", "concatenate", "stack", "where",
        "maximum", "minimum", "abs", "sqrt", "exp", "log", "sin", "cos",
        "pi", "nan", "inf", "int32", "int64", "float32", "float64", "bool_",
    ),
    "pandas": (
        "DataFrame", "Series", "read_csv", "read_excel", "read_json",
        "read_parquet", "concat", "merge", "to_datetime", "date_range",
        "Timestamp", "Timedelta", "NA", "isnull", "notnull", "get_dummies",
    ),
    "requests": (
        "get", "post", "put", "patch", "delete", "head", "options", "Session",
        "Response", "RequestException", "HTTPError", "Timeout", "exceptions",
    ),
    "flask": (
        "Flask", "request", "jsonify", "render_template", "redirect", "url_for",
        "abort", "session", "g", "Blueprint", "flash",
    ),
    "pytest": (
        "fixture", "mark", "raises", "approx", "main", "skip", "fail", "param",
    ),
    "PySide6": (
        "QtWidgets", "QtCore", "QtGui", "QApplication", "QWidget", "QMainWindow",
        "QPushButton", "QLabel", "QVBoxLayout", "QHBoxLayout", "QTimer",
        "Signal", "Slot", "QSettings", "QFileDialog", "QMessageBox",
    ),
}

PYTHON_EXTRA_MODULES = (
    "matplotlib", "scipy", "sklearn", "torch", "tensorflow", "PyQt6",
    "sqlalchemy", "pydantic", "aiohttp", "httpx", "click", "rich", "typer",
    "PIL", "cv2", "django", "fastapi", "uvicorn", "openai", "anthropic",
    "beautifulsoup4", "bs4", "lxml", "yaml", "dotenv", "redis", "celery",
)

PYTHON_COMMON_MODULES = (
    "os", "sys", "math", "json", "re", "pathlib", "datetime", "collections",
    "itertools", "random", "typing", "time", "subprocess", "threading",
    "asyncio", "socket", "sqlite3", "argparse", "csv", "unittest", "numpy",
    "pandas", "requests", "flask", "pytest", "PySide6",
)

# ---------------------------------------------------------------------------
# C / C++
# ---------------------------------------------------------------------------

C_HEADERS: dict[str, tuple[str, ...]] = {
    "assert.h": ("assert",),
    "ctype.h": (
        "isalnum", "isalpha", "isblank", "iscntrl", "isdigit", "isgraph",
        "islower", "isprint", "ispunct", "isspace", "isupper", "isxdigit",
        "tolower", "toupper",
    ),
    "errno.h": ("errno", "EINVAL", "ENOENT", "ENOMEM", "EACCES", "EEXIST"),
    "limits.h": (
        "CHAR_BIT", "CHAR_MIN", "CHAR_MAX", "SHRT_MIN", "SHRT_MAX",
        "INT_MIN", "INT_MAX", "LONG_MIN", "LONG_MAX", "UINT_MAX", "ULLONG_MAX",
    ),
    "math.h": (
        "sqrt", "pow", "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
        "log", "log10", "exp", "floor", "ceil", "round", "fabs", "fmod",
        "hypot", "isnan", "isinf", "M_PI", "M_E", "INFINITY", "NAN",
    ),
    "stdbool.h": ("bool", "true", "false"),
    "stddef.h": ("size_t", "ptrdiff_t", "wchar_t", "NULL", "offsetof"),
    "stdint.h": (
        "int8_t", "int16_t", "int32_t", "int64_t", "uint8_t", "uint16_t",
        "uint32_t", "uint64_t", "intptr_t", "uintptr_t", "intmax_t",
        "uintmax_t", "INT8_MAX", "INT16_MAX", "INT32_MAX", "INT64_MAX",
        "UINT8_MAX", "UINT16_MAX", "UINT32_MAX", "UINT64_MAX",
    ),
    "stdio.h": (
        "printf", "fprintf", "sprintf", "snprintf", "vprintf", "vfprintf",
        "scanf", "fscanf", "sscanf", "fopen", "fclose", "fread", "fwrite",
        "fgets", "fputs", "getchar", "putchar", "puts", "perror", "remove",
        "rename", "fflush", "fseek", "ftell", "rewind", "FILE", "stdin",
        "stdout", "stderr", "EOF", "SEEK_SET", "SEEK_CUR", "SEEK_END",
    ),
    "stdlib.h": (
        "malloc", "calloc", "realloc", "free", "exit", "abort", "atexit",
        "atoi", "atol", "atoll", "atof", "strtol", "strtoul", "strtod",
        "qsort", "bsearch", "rand", "srand", "abs", "labs", "llabs", "div",
        "ldiv", "EXIT_SUCCESS", "EXIT_FAILURE", "RAND_MAX", "NULL",
    ),
    "string.h": (
        "memcpy", "memmove", "memset", "memcmp", "strlen", "strcpy",
        "strncpy", "strcat", "strncat", "strcmp", "strncmp", "strchr",
        "strrchr", "strstr", "strtok", "strdup", "strerror",
    ),
    "time.h": (
        "time", "clock", "difftime", "mktime", "localtime", "gmtime",
        "strftime", "time_t", "clock_t", "tm", "CLOCKS_PER_SEC",
    ),
    "unistd.h": (
        "read", "write", "close", "fork", "getpid", "sleep", "usleep",
        "chdir", "getcwd", "access", "unlink", "pipe", "dup", "dup2",
    ),
    "pthread.h": (
        "pthread_t", "pthread_create", "pthread_join", "pthread_exit",
        "pthread_mutex_t", "pthread_mutex_init", "pthread_mutex_lock",
        "pthread_mutex_unlock", "pthread_cond_t", "pthread_cond_wait",
    ),
    "sys/types.h": (
        "size_t", "ssize_t", "off_t", "pid_t", "mode_t", "uid_t", "gid_t",
        "dev_t", "ino_t",
    ),
    "sys/socket.h": (
        "socket", "bind", "listen", "accept", "connect", "send", "recv",
        "setsockopt", "getsockopt", "shutdown", "socklen_t", "sockaddr",
        "AF_INET", "AF_INET6", "SOCK_STREAM", "SOCK_DGRAM",
    ),
    "arpa/inet.h": (
        "inet_ntoa", "inet_addr", "inet_pton", "inet_ntop", "htons", "ntohs",
        "htonl", "ntohl",
    ),
    "fcntl.h": ("open", "creat", "fcntl", "O_RDONLY", "O_WRONLY", "O_RDWR", "O_CREAT"),
}

CPP_HEADERS: dict[str, tuple[str, ...]] = {
    "algorithm": (
        "sort", "stable_sort", "find", "find_if", "reverse", "accumulate",
        "max", "min", "count", "count_if", "unique", "binary_search",
        "lower_bound", "upper_bound", "next_permutation",
    ),
    "array": ("array", "get", "tuple_size"),
    "chrono": (
        "chrono", "seconds", "milliseconds", "microseconds", "nanoseconds",
        "steady_clock", "system_clock", "duration_cast",
    ),
    "cmath": (
        "sqrt", "pow", "sin", "cos", "tan", "log", "exp", "floor", "ceil",
        "round", "fabs", "hypot", "isnan", "isinf",
    ),
    "filesystem": (
        "filesystem", "path", "directory_iterator", "recursive_directory_iterator",
        "exists", "create_directory", "remove", "rename",
    ),
    "fstream": (
        "ifstream", "ofstream", "fstream", "ios", "ios_base", "getline",
    ),
    "functional": (
        "function", "bind", "ref", "cref", "hash", "less", "greater",
    ),
    "iostream": ("cout", "cin", "cerr", "clog", "endl", "ends", "flush"),
    "map": ("map", "multimap", "unordered_map", "unordered_multimap"),
    "memory": (
        "shared_ptr", "unique_ptr", "weak_ptr", "make_shared", "make_unique",
        "allocator", "enable_shared_from_this",
    ),
    "mutex": (
        "mutex", "recursive_mutex", "lock_guard", "unique_lock", "scoped_lock",
    ),
    "numeric": ("accumulate", "iota", "gcd", "lcm", "inner_product", "partial_sum"),
    "optional": ("optional", "nullopt", "make_optional"),
    "queue": ("queue", "priority_queue", "deque"),
    "random": (
        "random_device", "mt19937", "uniform_int_distribution",
        "uniform_real_distribution", "shuffle",
    ),
    "regex": ("regex", "smatch", "cmatch", "regex_match", "regex_search", "regex_replace"),
    "set": ("set", "multiset", "unordered_set", "unordered_multiset"),
    "sstream": ("stringstream", "istringstream", "ostringstream", "getline"),
    "stack": ("stack",),
    "string": ("string", "wstring", "string_view", "stoi", "stol", "stod", "to_string"),
    "thread": ("thread", "this_thread", "sleep_for", "sleep_until"),
    "tuple": ("tuple", "make_tuple", "tie", "get", "tuple_size"),
    "unordered_map": ("unordered_map", "unordered_multimap"),
    "utility": ("pair", "make_pair", "move", "forward", "swap", "exchange"),
    "variant": ("variant", "visit", "get", "holds_alternative", "monostate"),
    "vector": (
        "vector", "push_back", "emplace_back", "reserve", "resize", "at",
        "front", "back", "begin", "end", "insert", "erase", "clear",
    ),
}

C_HEADER_ORDER = (
    "stdio.h", "stdlib.h", "string.h", "math.h", "stdint.h", "stdbool.h",
    "stddef.h", "time.h", "ctype.h", "errno.h", "assert.h", "limits.h",
    "unistd.h", "sys/types.h", "sys/socket.h", "arpa/inet.h", "pthread.h",
    "fcntl.h",
)

CPP_HEADER_ORDER = (
    "iostream", "vector", "string", "map", "unordered_map", "set",
    "algorithm", "memory", "fstream", "sstream", "optional", "variant",
    "array", "deque", "list", "queue", "stack", "tuple", "utility",
    "functional", "numeric", "chrono", "filesystem", "thread", "mutex",
    "regex", "random", "cmath",
)

CPP_STD_SYMBOLS = (
    "cout", "cin", "cerr", "clog", "endl", "flush", "vector", "string",
    "string_view", "map", "unordered_map", "set", "unordered_set", "array",
    "deque", "list", "queue", "stack", "pair", "tuple", "optional", "variant",
    "any", "shared_ptr", "unique_ptr", "weak_ptr", "make_shared",
    "make_unique", "sort", "find", "reverse", "move", "forward", "swap",
    "size", "begin", "end", "to_string", "stoi", "stol", "stod", "getline",
    "thread", "mutex", "chrono", "filesystem", "regex", "function",
    "accumulate", "max", "min", "numeric_limits", "span",
)

# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

JAVA_IMPORT_SYMBOLS: dict[str, tuple[str, ...]] = {
    "java.util": (
        "List", "ArrayList", "LinkedList", "Map", "HashMap", "LinkedHashMap",
        "TreeMap", "Set", "HashSet", "LinkedHashSet", "TreeSet", "Collection",
        "Collections", "Arrays", "Optional", "Scanner", "Random", "Date",
        "Calendar", "UUID", "Objects", "Comparator", "Iterator", "Queue",
        "Deque", "ArrayDeque", "PriorityQueue",
    ),
    "java.util.stream": ("Stream", "Collectors", "IntStream", "LongStream", "DoubleStream"),
    "java.io": (
        "File", "FileReader", "FileWriter", "BufferedReader", "BufferedWriter",
        "InputStream", "OutputStream", "InputStreamReader", "OutputStreamWriter",
        "PrintWriter", "IOException", "EOFException", "FileInputStream",
        "FileOutputStream",
    ),
    "java.nio.file": ("Path", "Paths", "Files", "StandardOpenOption", "FileSystems"),
    "java.time": (
        "LocalDate", "LocalTime", "LocalDateTime", "ZonedDateTime", "Instant",
        "Duration", "Period", "DateTimeFormatter", "ZoneId",
    ),
    "java.util.concurrent": (
        "ExecutorService", "Executors", "Future", "CompletableFuture",
        "TimeUnit", "CountDownLatch", "Semaphore", "ConcurrentHashMap",
        "BlockingQueue", "LinkedBlockingQueue",
    ),
    "java.net": ("Socket", "ServerSocket", "URI", "URL", "HttpURLConnection"),
    "java.net.http": ("HttpClient", "HttpRequest", "HttpResponse"),
    "java.sql": (
        "Connection", "DriverManager", "ResultSet", "PreparedStatement",
        "Statement", "SQLException",
    ),
    "java.math": ("BigInteger", "BigDecimal"),
    "java.util.regex": ("Pattern", "Matcher"),
    "java.util.function": (
        "Function", "BiFunction", "Consumer", "Supplier", "Predicate",
        "UnaryOperator", "BinaryOperator",
    ),
    "java.util.concurrent.atomic": (
        "AtomicInteger", "AtomicLong", "AtomicBoolean", "AtomicReference",
    ),
}

JAVA_IMPORTS = tuple(
    f"{package}.{symbol}"
    for package, symbols in JAVA_IMPORT_SYMBOLS.items()
    for symbol in symbols
)

# ---------------------------------------------------------------------------
# JavaScript / TypeScript
# ---------------------------------------------------------------------------

JS_PACKAGES: dict[str, tuple[str, ...]] = {
    "fs": (
        "readFile", "readFileSync", "writeFile", "writeFileSync", "appendFile",
        "mkdir", "mkdirSync", "readdir", "readdirSync", "stat", "statSync",
        "existsSync", "unlink", "unlinkSync", "createReadStream",
        "createWriteStream", "promises",
    ),
    "path": (
        "join", "resolve", "basename", "dirname", "extname", "relative",
        "isAbsolute", "normalize", "sep", "parse", "format",
    ),
    "os": (
        "platform", "arch", "cpus", "homedir", "tmpdir", "hostname", "type",
        "release", "totalmem", "freemem", "EOL",
    ),
    "http": ("createServer", "request", "get", "Server", "IncomingMessage", "ServerResponse"),
    "https": ("createServer", "request", "get", "Agent"),
    "url": ("URL", "URLSearchParams", "parse", "format", "resolve"),
    "util": ("promisify", "inspect", "format", "types", "TextEncoder", "TextDecoder"),
    "events": ("EventEmitter", "once", "on"),
    "stream": (
        "Readable", "Writable", "Duplex", "Transform", "PassThrough",
        "pipeline", "finished",
    ),
    "child_process": ("exec", "execSync", "spawn", "spawnSync", "fork", "execFile"),
    "crypto": (
        "randomBytes", "randomUUID", "createHash", "createHmac",
        "createCipheriv", "createDecipheriv", "timingSafeEqual",
    ),
    "readline": ("createInterface", "Interface"),
    "zlib": ("gzip", "gunzip", "gzipSync", "gunzipSync", "deflate", "inflate"),
    "assert": ("strict", "equal", "deepEqual", "ok", "throws", "rejects"),
    "buffer": ("Buffer", "alloc", "from", "concat"),
    "process": (
        "argv", "env", "exit", "cwd", "stdout", "stderr", "stdin", "platform",
        "version",
    ),
    "react": (
        "useState", "useEffect", "useMemo", "useCallback", "useRef",
        "useContext", "useReducer", "useLayoutEffect", "createContext",
        "createElement", "Component", "Fragment", "StrictMode", "Suspense",
        "memo", "forwardRef",
    ),
    "react-dom": ("createRoot", "render", "hydrateRoot"),
    "express": ("Router", "json", "urlencoded", "static", "Request", "Response", "NextFunction"),
    "axios": ("get", "post", "put", "patch", "delete", "head", "options", "create", "AxiosError"),
    "lodash": (
        "map", "filter", "reduce", "forEach", "find", "findIndex", "some",
        "every", "debounce", "throttle", "cloneDeep", "merge", "pick", "omit",
        "get", "set", "uniq", "sortBy", "groupBy",
    ),
    "dotenv": ("config", "parse"),
    "chalk": ("red", "green", "blue", "yellow", "cyan", "magenta", "white", "gray", "bold"),
}

JS_MODULES = tuple(JS_PACKAGES) + (
    "node:fs", "node:path", "node:os", "node:http", "node:https", "node:url",
    "node:util", "node:events", "node:stream", "node:child_process",
    "node:crypto", "node:buffer", "node:process", "node:assert", "node:zlib",
    "node:readline",
)

# ---------------------------------------------------------------------------
# Go
# ---------------------------------------------------------------------------

GO_PACKAGES: dict[str, tuple[str, ...]] = {
    "fmt": (
        "Print", "Printf", "Println", "Sprint", "Sprintf", "Sprintln",
        "Errorf", "Fprint", "Fprintf", "Fprintln", "Scan", "Scanf", "Scanln",
        "Sscan", "Sscanf",
    ),
    "os": (
        "Args", "Exit", "Getenv", "Setenv", "Environ", "Open", "Create",
        "ReadFile", "WriteFile", "Remove", "Mkdir", "MkdirAll", "Stat",
        "Stdout", "Stderr", "Stdin", "Getpid",
    ),
    "io": ("Reader", "Writer", "ReadAll", "Copy", "CopyN", "EOF", "ReadCloser", "WriteCloser"),
    "strings": (
        "Contains", "HasPrefix", "HasSuffix", "Split", "Join", "Replace",
        "ReplaceAll", "ToLower", "ToUpper", "TrimSpace", "Fields", "Builder",
        "NewReader", "Repeat",
    ),
    "strconv": ("Atoi", "Itoa", "ParseInt", "ParseUint", "ParseFloat", "FormatInt", "FormatFloat", "Quote", "Unquote"),
    "math": ("Sqrt", "Pow", "Sin", "Cos", "Tan", "Abs", "Max", "Min", "Floor", "Ceil", "Round", "Pi", "Inf", "NaN"),
    "time": ("Now", "Sleep", "Since", "Until", "Unix", "Duration", "Time", "Second", "Millisecond", "Minute", "Hour"),
    "sync": ("WaitGroup", "Mutex", "RWMutex", "Once", "Map", "Cond"),
    "context": ("Background", "TODO", "WithCancel", "WithTimeout", "WithDeadline", "WithValue", "Context"),
    "errors": ("New", "Is", "As", "Unwrap", "Join"),
    "log": ("Print", "Printf", "Println", "Fatal", "Fatalf", "Fatalln", "Panic", "New", "SetFlags"),
    "sort": ("Ints", "Strings", "Float64s", "Slice", "SliceStable", "Sort", "Search", "IsSorted"),
    "bytes": ("Buffer", "NewBuffer", "Contains", "Equal", "HasPrefix", "Split", "Join"),
    "bufio": ("Reader", "Writer", "NewReader", "NewWriter", "Scanner", "ReadString", "WriteString"),
    "regexp": ("MustCompile", "Compile", "MatchString", "QuoteMeta", "Regexp"),
    "path": ("Join", "Base", "Dir", "Ext", "Clean", "IsAbs", "Match"),
    "filepath": ("Join", "Base", "Dir", "Ext", "Abs", "Clean", "Walk", "Glob", "Rel"),
    "net": ("Dial", "Listen", "Conn", "IP", "TCPAddr", "UDPAddr"),
    "http": ("Get", "Post", "PostForm", "Head", "ListenAndServe", "HandleFunc", "Handle", "Client", "Request", "Response", "ResponseWriter"),
    "url": ("Parse", "QueryEscape", "QueryUnescape", "PathEscape", "URL", "Values"),
    "json": ("Marshal", "Unmarshal", "NewEncoder", "NewDecoder", "Encoder", "Decoder", "RawMessage"),
    "csv": ("Reader", "Writer", "NewReader", "NewWriter"),
    "xml": ("Marshal", "Unmarshal", "NewEncoder", "NewDecoder", "Encoder", "Decoder"),
    "sql": ("Open", "DB", "Tx", "Stmt", "Row", "Rows", "NullString", "NullInt64"),
    "flag": ("String", "Int", "Bool", "Float64", "Parse", "Args", "NArg"),
    "testing": ("T", "B", "F", "Run", "Short", "Error", "Errorf", "Fatal", "Fatalf"),
    "reflect": ("TypeOf", "ValueOf", "Type", "Value", "DeepEqual"),
    "runtime": ("GC", "GOOS", "GOARCH", "NumCPU", "NumGoroutine", "Version"),
    "unicode": ("IsLetter", "IsDigit", "IsSpace", "IsUpper", "IsLower", "ToUpper", "ToLower"),
    "utf8": ("Valid", "RuneLen", "RuneCount", "DecodeRune", "EncodeRune", "RuneError"),
    "rand": ("Intn", "Int", "Float64", "Seed", "Shuffle", "New", "Rand"),
    "exec": ("Command", "CommandContext", "Run", "Output", "CombinedOutput", "Start"),
    "signal": ("Notify", "Stop", "NotifyContext", "Ignore"),
    "atomic": ("AddInt32", "AddInt64", "LoadInt32", "LoadInt64", "StoreInt32", "StoreInt64", "CompareAndSwapInt32"),
}

GO_IMPORT_PATHS = (
    "fmt", "os", "io", "strings", "strconv", "math", "math/rand", "time",
    "sync", "sync/atomic", "context", "errors", "log", "sort", "bytes",
    "bufio", "regexp", "path", "path/filepath", "net", "net/http", "net/url",
    "encoding/json", "encoding/csv", "encoding/xml", "database/sql", "flag",
    "testing", "reflect", "runtime", "unicode", "unicode/utf8", "os/exec",
    "os/signal",
)

# ---------------------------------------------------------------------------
# Rust
# ---------------------------------------------------------------------------

RUST_USE_PATHS = (
    "std::collections::HashMap", "std::collections::HashSet",
    "std::collections::BTreeMap", "std::collections::BTreeSet",
    "std::collections::VecDeque", "std::collections::BinaryHeap",
    "std::collections::LinkedList", "std::fs::File",
    "std::fs::read_to_string", "std::fs::write", "std::fs::read_dir",
    "std::fs::create_dir", "std::fs::remove_file", "std::fs::metadata",
    "std::io::Read", "std::io::Write", "std::io::BufReader",
    "std::io::BufWriter", "std::io::stdin", "std::io::stdout",
    "std::io::stderr", "std::io::Cursor", "std::io::Error",
    "std::path::Path", "std::path::PathBuf", "std::sync::Arc",
    "std::sync::Mutex", "std::sync::RwLock", "std::sync::mpsc",
    "std::sync::OnceLock", "std::sync::atomic::AtomicBool",
    "std::sync::atomic::AtomicUsize", "std::sync::atomic::Ordering",
    "std::thread", "std::thread::spawn", "std::thread::sleep",
    "std::time::Duration", "std::time::Instant", "std::time::SystemTime",
    "std::env", "std::env::args", "std::env::var", "std::env::set_var",
    "std::process::Command", "std::process::Stdio", "std::process::ExitCode",
    "std::net::TcpListener", "std::net::TcpStream", "std::net::UdpSocket",
    "std::net::IpAddr", "std::fmt", "std::fmt::Debug", "std::fmt::Display",
    "std::fmt::Formatter", "std::error::Error", "std::result::Result",
    "std::option::Option", "std::mem", "std::ptr", "std::cmp",
    "std::cmp::Ordering", "std::iter", "std::str", "std::string::String",
    "std::vec::Vec", "std::boxed::Box", "std::rc::Rc", "std::cell::RefCell",
    "std::convert::From", "std::convert::Into", "std::ops::Add",
    "std::ops::Deref", "std::hash::Hash", "std::marker::PhantomData",
    "std::any::Any", "serde::Serialize", "serde::Deserialize",
    "serde::de", "serde::ser", "serde_json::Value", "serde_json::from_str",
    "serde_json::to_string", "tokio::main", "tokio::spawn", "tokio::time",
    "tokio::sync", "tokio::runtime", "tokio::net", "tokio::fs", "tokio::io",
    "tokio::task", "tokio::select", "tokio::join", "tokio::try_join",
    "rand::prelude", "rand::Rng", "rand::thread_rng", "rand::random",
    "rand::seq", "rand::distributions", "regex::Regex",
    "regex::RegexBuilder", "regex::escape",
)

RUST_TYPE_MEMBERS: dict[str, tuple[str, ...]] = {
    "HashMap": (
        "new", "with_capacity", "from", "default", "insert", "get", "get_mut",
        "remove", "contains_key", "entry", "iter", "iter_mut", "keys", "values",
        "len", "is_empty", "clear", "extend", "retain", "drain", "capacity",
        "reserve", "shrink_to_fit",
    ),
    "HashSet": (
        "new", "with_capacity", "from", "default", "insert", "remove",
        "contains", "iter", "len", "is_empty", "clear", "extend", "retain",
        "drain", "capacity", "reserve",
    ),
    "BTreeMap": (
        "new", "from", "default", "insert", "get", "get_mut", "remove",
        "contains_key", "entry", "iter", "iter_mut", "keys", "values", "len",
        "is_empty", "clear", "extend", "range", "first_key_value",
        "last_key_value",
    ),
    "BTreeSet": (
        "new", "from", "default", "insert", "remove", "contains", "iter",
        "len", "is_empty", "clear", "extend", "range", "first", "last",
    ),
    "VecDeque": (
        "new", "with_capacity", "from", "push_front", "push_back", "pop_front",
        "pop_back", "front", "back", "iter", "len", "is_empty", "clear",
        "insert", "remove", "rotate_left", "rotate_right", "reserve",
    ),
    "BinaryHeap": (
        "new", "with_capacity", "from", "push", "pop", "peek", "peek_mut",
        "len", "is_empty", "clear", "into_sorted_vec",
    ),
    "LinkedList": (
        "new", "push_front", "push_back", "pop_front", "pop_back", "front",
        "back", "iter", "len", "is_empty", "clear",
    ),
    "Vec": (
        "new", "with_capacity", "from", "from_elem", "from_raw_parts", "push",
        "pop", "insert", "remove", "get", "get_mut", "iter", "iter_mut",
        "len", "is_empty", "clear", "truncate", "resize", "reserve",
        "shrink_to_fit", "sort", "sort_by", "dedup", "extend",
        "extend_from_slice", "split_off", "append", "drain", "retain",
        "as_slice", "as_mut_slice", "first", "last", "contains",
    ),
    "String": (
        "new", "with_capacity", "from", "from_utf8", "from_utf8_lossy",
        "from_utf16", "from_utf16_lossy", "from_utf8_unchecked", "push",
        "push_str", "pop", "insert", "insert_str", "remove", "truncate",
        "clear", "len", "is_empty", "as_str", "as_bytes", "as_mut_str",
        "split", "split_whitespace", "trim", "to_lowercase", "to_uppercase",
        "replace", "contains", "starts_with", "ends_with", "find", "rfind",
        "parse", "capacity", "reserve", "shrink_to_fit",
    ),
    "Path": (
        "new", "from", "exists", "is_file", "is_dir", "is_absolute",
        "is_relative", "join", "parent", "file_name", "file_stem", "extension",
        "with_extension", "with_file_name", "display", "to_str",
        "to_string_lossy", "canonicalize", "metadata", "read_dir", "components",
        "ancestors", "starts_with", "ends_with",
    ),
    "PathBuf": (
        "new", "from", "with_capacity", "push", "pop", "set_file_name",
        "set_extension", "as_path", "into_os_string", "capacity", "reserve",
        "clear",
    ),
    "File": (
        "open", "create", "create_new", "options", "from", "open_options",
        "metadata", "set_len", "sync_all", "sync_data", "try_clone",
        "read_to_string", "write_all",
    ),
    "OpenOptions": (
        "new", "read", "write", "append", "truncate", "create", "create_new",
        "open",
    ),
    "Command": (
        "new", "arg", "args", "env", "envs", "current_dir", "stdin", "stdout",
        "stderr", "spawn", "output", "status", "wait", "kill",
    ),
    "Stdio": ("null", "inherit", "piped"),
    "Duration": (
        "from_secs", "from_millis", "from_micros", "from_nanos",
        "from_secs_f64", "from_secs_f32", "new", "as_secs", "as_millis",
        "as_micros", "as_nanos", "as_secs_f64", "as_secs_f32", "checked_add",
        "checked_sub", "saturating_add", "saturating_sub", "ZERO", "MAX",
    ),
    "Instant": (
        "now", "elapsed", "duration_since", "checked_duration_since",
        "checked_add", "checked_sub",
    ),
    "SystemTime": (
        "now", "elapsed", "duration_since", "checked_add", "checked_sub",
        "UNIX_EPOCH",
    ),
    "Arc": (
        "new", "try_new", "new_uninit", "new_zeroed", "strong_count",
        "weak_count", "ptr_eq", "get_mut", "make_mut", "downgrade",
        "try_unwrap", "into_raw", "from_raw",
    ),
    "Rc": (
        "new", "strong_count", "weak_count", "ptr_eq", "get_mut", "make_mut",
        "downgrade", "try_unwrap", "into_raw", "from_raw",
    ),
    "Mutex": ("new", "lock", "try_lock", "get_mut", "into_inner", "const_new"),
    "RwLock": (
        "new", "read", "write", "try_read", "try_write", "get_mut",
        "into_inner", "const_new",
    ),
    "OnceLock": ("new", "get", "get_or_init", "get_or_try_init", "set", "take", "get_mut"),
    "TcpStream": (
        "connect", "connect_timeout", "peer_addr", "local_addr",
        "set_read_timeout", "set_write_timeout", "read", "write", "shutdown",
        "try_clone", "set_nodelay",
    ),
    "TcpListener": (
        "bind", "accept", "local_addr", "set_nonblocking", "incoming",
        "try_clone", "ttl",
    ),
    "UdpSocket": (
        "bind", "connect", "send_to", "recv_from", "local_addr", "peer_addr",
        "set_read_timeout", "set_write_timeout", "try_clone",
    ),
    "Regex": (
        "new", "new_multi_line", "is_match", "find", "find_iter", "captures",
        "captures_iter", "replace", "replace_all", "replacen", "split",
        "splitn", "captures_len", "as_str",
    ),
    "RegexBuilder": (
        "new", "case_insensitive", "multi_line", "dot_matches_new_line",
        "ignore_whitespace", "unicode", "size_limit", "dfa_size_limit",
        "build",
    ),
    "Option": (
        "Some", "None", "is_some", "is_none", "unwrap", "unwrap_or",
        "unwrap_or_else", "map", "and_then", "or_else", "ok_or",
        "ok_or_else", "take", "replace", "as_ref", "as_mut",
    ),
    "Result": (
        "Ok", "Err", "is_ok", "is_err", "unwrap", "unwrap_err", "unwrap_or",
        "unwrap_or_else", "map", "map_err", "and_then", "or_else", "ok", "err",
        "as_ref", "as_mut",
    ),
    "Ordering": (
        "Less", "Equal", "Greater", "reverse", "then", "is_lt", "is_eq",
        "is_gt",
    ),
    "Box": (
        "new", "new_uninit", "new_zeroed", "pin", "leak", "into_raw",
        "from_raw", "try_new",
    ),
    "RefCell": (
        "new", "borrow", "borrow_mut", "try_borrow", "try_borrow_mut",
        "get_mut", "into_inner", "replace", "swap", "take",
    ),
    "Cell": (
        "new", "get", "set", "replace", "take", "swap", "as_ptr", "get_mut",
        "into_inner",
    ),
    "Default": ("default",),
    "From": ("from",),
    "Into": ("into",),
    "Value": (
        "Null", "Bool", "Number", "String", "Array", "Object", "as_str",
        "as_i64", "as_u64", "as_f64", "as_bool", "as_array", "as_object",
        "is_null", "is_string", "is_number", "is_boolean", "is_array",
        "is_object", "get", "get_mut", "take",
    ),
}

# ---------------------------------------------------------------------------
# C#
# ---------------------------------------------------------------------------

CS_NAMESPACES = (
    "System", "System.Collections", "System.Collections.Generic",
    "System.IO", "System.Linq", "System.Text", "System.Text.Json",
    "System.Threading", "System.Threading.Tasks", "System.Net",
    "System.Net.Http", "System.Diagnostics", "System.Globalization",
    "System.Security.Cryptography", "System.Reflection", "System.Runtime",
)

# ---------------------------------------------------------------------------
# Ruby / Lua / PHP
# ---------------------------------------------------------------------------

RUBY_REQUIRES = (
    "json", "yaml", "csv", "set", "date", "time", "securerandom", "digest",
    "base64", "uri", "net/http", "open-uri", "fileutils", "pathname",
    "logger", "tempfile", "stringio", "socket", "openssl", "zlib",
    "benchmark", "optparse", "shellwords", "timeout", "io/console", "erb",
    "racc", "rexml/document", "bigdecimal", "matrix",
)

LUA_MODULES = (
    "json", "socket", "lfs", "lpeg", "cjson", "http", "https", "sqlite3",
    "uuid", "re", "inspect", "pl.path", "pl.tablex", "pl.stringx", "dkjson",
    "luasql", "digest", "crypto", "ssl", "utf8",
)

PHP_NAMESPACES = (
    "Psr\\Log\\LoggerInterface", "Psr\\Http\\Message\\RequestInterface",
    "Psr\\Http\\Message\\ResponseInterface", "Psr\\Container\\ContainerInterface",
    "Symfony\\Component\\HttpFoundation\\Request",
    "Symfony\\Component\\HttpFoundation\\Response",
    "Illuminate\\Support\\Collection", "Illuminate\\Support\\Facades\\DB",
    "Doctrine\\ORM\\EntityManagerInterface", "Monolog\\Logger",
    "GuzzleHttp\\Client",
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _prefix_matches(
    items: tuple[str, ...] | list[str],
    prefix: str,
    *,
    allow_exact: bool = False,
) -> list[str]:
    lowered = prefix.lower()
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        if lowered and not key.startswith(lowered):
            continue
        if not allow_exact and lowered and key == lowered:
            continue
        seen.add(key)
        result.append(item)
    return result


def _quoted(items: tuple[str, ...], prefix: str, quote: str) -> list[str]:
    return [
        f"{item}{quote}"
        for item in _prefix_matches(items, prefix, allow_exact=True)
    ]


@lru_cache(maxsize=1)
def python_module_names() -> tuple[str, ...]:
    names = {
        name
        for name in getattr(sys, "stdlib_module_names", ())
        if name and not name.startswith("_")
    }
    try:
        for module in pkgutil.iter_modules():
            name = module.name
            if name and not name.startswith("_") and name.isidentifier():
                names.add(name)
    except Exception:
        pass
    names.update(PYTHON_LIBRARIES)
    names.update(PYTHON_EXTRA_MODULES)
    ordered: list[str] = []
    seen: set[str] = set()
    for group in (
        PYTHON_COMMON_MODULES,
        PYTHON_EXTRA_MODULES,
        tuple(PYTHON_LIBRARIES),
        tuple(sorted(names, key=str.lower)),
    ):
        for name in group:
            key = name.lower()
            if key in seen or name not in names:
                continue
            seen.add(key)
            ordered.append(name)
    return tuple(ordered)


# ---------------------------------------------------------------------------
# Context token detection
# ---------------------------------------------------------------------------


def _go_import_block_open(text: str, line_index: int) -> bool:
    if line_index <= 0:
        return False
    depth = 0
    for line in text.splitlines()[:line_index]:
        stripped = line.strip()
        if stripped.startswith("import ("):
            depth += 1
        elif depth and stripped.startswith(")"):
            depth -= 1
    return depth > 0


def _rust_use_parts(before: str) -> tuple[list[str], str, bool] | None:
    """Split a Rust use line into its current brace base and item prefix."""
    match = re.match(r"^\s*(?:pub\s+)?use\s+", before)
    if not match:
        return None
    rest = before[match.end():]
    base: list[str] = []
    stack: list[list[str]] = []
    item: list[str] = []
    brace_seen = False
    for char in rest:
        if char == "{":
            brace_seen = True
            stack.append(list(base))
            extra = "".join(item).strip()
            if extra:
                base.extend(part for part in extra.split("::") if part)
            item.clear()
        elif char == "}":
            if stack:
                base = stack.pop()
            item.clear()
        elif char == ",":
            item.clear()
        else:
            item.append(char)
    return base, "".join(item).lstrip(), brace_seen


def context_token(
    language: str,
    before: str,
    text: str = "",
    line_index: int = -1,
) -> str | None:
    """Return a library-aware token at the cursor, or None for normal code."""
    if language == "python":
        if before.lstrip().startswith("#"):
            return None
        match = re.match(r"^\s*from\s+([\w.]*)$", before)
        if match:
            return match.group(1)
        if re.match(r"^\s*from\s+[\w.]+\s+import\s*$", before):
            return ""
        match = re.match(r"^\s*import\s+([\w.]*)$", before)
        if match:
            return match.group(1)
        if re.search(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\.\s*$", before):
            return ""
        return None

    if language in ("c", "cpp"):
        match = re.match(r'^\s*#\s*include\s*[<"]([^>"]*)$', before)
        if match:
            return match.group(1)
        if language == "cpp" and re.search(r"\bstd\s*::\s*$", before):
            return ""
        return None

    if language == "java":
        match = re.match(r"^\s*import\s+(?:static\s+)?([\w.*]*)$", before)
        if match:
            return match.group(1)
        return None

    if language in ("javascript", "typescript"):
        for pattern in (
            r'\bfrom\s*([\'"])([^\'"]*)$',
            r'^\s*import\s*([\'"])([^\'"]*)$',
            r'\b(?:require|import)\s*\(\s*([\'"])([^\'"]*)$',
        ):
            match = re.search(pattern, before)
            if match:
                return match.group(2)
        if re.search(r"[A-Za-z_$]\w*\.\s*$", before):
            return ""
        return None

    if language == "go":
        match = re.match(r'^\s*import\s+(?:\w+\s+)?([\'"])([^\'"]*)$', before)
        if match:
            return match.group(2)
        if _go_import_block_open(text, line_index):
            match = re.match(r'^\s*(?:\w+\s+)?([\'"])([^\'"]*)$', before)
            if match:
                return match.group(2)
        if re.search(r"[A-Za-z_]\w*\.\s*$", before):
            return ""
        return None

    if language == "rust":
        parts = _rust_use_parts(before)
        if parts is not None:
            _base, item, _brace_seen = parts
            return item
        if re.search(r"(?:[A-Za-z_]\w*::)+\s*$", before):
            return ""
        return None

    if language == "csharp":
        match = re.match(r"^\s*using\s+(?:static\s+)?([\w.]*)$", before)
        if match and match.group(1) not in ("var",):
            return match.group(1)
        return None

    if language == "ruby":
        match = re.search(r'\brequire\s*\(?\s*([\'"])([^\'"]*)$', before)
        if match:
            return match.group(2)
        return None

    if language == "lua":
        match = re.search(r'\brequire\s*\(?\s*([\'"])([^\'"]*)$', before)
        if match:
            return match.group(2)
        return None

    if language == "php":
        match = re.match(r"^\s*use\s+([\w\\]*)$", before)
        if match:
            return match.group(1)
        return None

    return None

# ---------------------------------------------------------------------------
# Import parsing
# ---------------------------------------------------------------------------

_PY_IMPORT_RE = re.compile(r"^\s*import\s+(.+)$")
_PY_FROM_RE = re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(.+)$")
_C_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE)
_JAVA_IMPORT_RE = re.compile(
    r"^\s*import\s+(?:static\s+)?([\w.]+)(\.\*)?\s*;", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(
    r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
)
_JS_NAMESPACE_RE = re.compile(
    r"import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
)
_JS_NAMED_RE = re.compile(
    r"import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]"
)
_JS_REQUIRE_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_JS_REQUIRE_NAMED_RE = re.compile(
    r"(?:const|let|var)\s*\{([^}]*)\}\s*=\s*require\(\s*['\"]([^'\"]+)['\"]\s*\)"
)
_GO_IMPORT_RE = re.compile(
    r'^\s*import\s+(?:(\w+|\.|_)\s+)?["\']([^"\']+)["\']', re.MULTILINE
)
_GO_BLOCK_IMPORT_RE = re.compile(
    r'^\s*(?:(\w+|\.|_)\s+)?["\']([^"\']+)["\']', re.MULTILINE
)


def _python_imports(text: str) -> tuple[dict[str, str], list[str]]:
    aliases: dict[str, str] = {}
    symbols: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = _PY_IMPORT_RE.match(line)
        if match:
            for part in match.group(1).split(","):
                bits = part.strip().split()
                if not bits:
                    continue
                module = bits[0]
                symbols.extend(PYTHON_LIBRARIES.get(module, ()))
                if len(bits) >= 3 and bits[1] == "as":
                    aliases[bits[2]] = module
                else:
                    root = module.split(".", 1)[0]
                    aliases.setdefault(root, root)
            continue
        match = _PY_FROM_RE.match(line)
        if match:
            module = match.group(1)
            symbols.extend(PYTHON_LIBRARIES.get(module, ()))
            for part in match.group(2).split(","):
                bits = part.strip().split()
                if bits and bits[0].isidentifier():
                    symbols.append(bits[0])
    return aliases, symbols


def _c_imported_symbols(language: str, text: str) -> list[str]:
    symbols: list[str] = []
    headers = C_HEADERS if language == "c" else {**C_HEADERS, **CPP_HEADERS}
    for match in _C_INCLUDE_RE.finditer(text):
        symbols.extend(headers.get(match.group(1), ()))
    return symbols


def _java_imported_symbols(text: str) -> list[str]:
    symbols: list[str] = []
    for match in _JAVA_IMPORT_RE.finditer(text):
        path = match.group(1)
        if match.group(2):
            symbols.extend(JAVA_IMPORT_SYMBOLS.get(path, ()))
        else:
            symbols.append(path.rsplit(".", 1)[-1])
    return symbols


def _js_package_symbols(package: str) -> tuple[str, ...]:
    key = package[5:] if package.startswith("node:") else package
    return JS_PACKAGES.get(key, ())


def _js_imports(text: str) -> tuple[dict[str, str], list[str]]:
    aliases: dict[str, str] = {}
    symbols: list[str] = []
    for match in _JS_NAMESPACE_RE.finditer(text):
        aliases[match.group(1)] = match.group(2)
    for match in _JS_IMPORT_RE.finditer(text):
        aliases[match.group(1)] = match.group(2)
    for match in _JS_REQUIRE_RE.finditer(text):
        aliases[match.group(1)] = match.group(2)
    for match in _JS_NAMED_RE.finditer(text):
        for part in match.group(1).split(","):
            bits = part.strip().split()
            if bits and bits[0].isidentifier():
                symbols.append(bits[-1] if len(bits) >= 3 else bits[0])
    for match in _JS_REQUIRE_NAMED_RE.finditer(text):
        for part in match.group(1).split(","):
            bits = part.strip().split()
            if bits and bits[0].isidentifier():
                symbols.append(bits[-1] if len(bits) >= 3 else bits[0])
    return aliases, symbols


def _go_aliases(text: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for match in _GO_IMPORT_RE.finditer(text):
        alias, path = match.group(1), match.group(2)
        key = path.rsplit("/", 1)[-1]
        if alias and alias not in (".", "_"):
            aliases[alias] = key
        else:
            aliases[key] = key
    for block_match in re.finditer(r"import\s*\((.*?)\)", text, re.DOTALL):
        for match in _GO_BLOCK_IMPORT_RE.finditer(block_match.group(1)):
            alias, path = match.group(1), match.group(2)
            key = path.rsplit("/", 1)[-1]
            if alias and alias not in (".", "_"):
                aliases[alias] = key
            else:
                aliases[key] = key
    return aliases


def library_imported_symbols(language: str, text: str, token: str) -> list[str]:
    """Symbols made available by imports/includes in the current file."""
    if language == "python":
        _aliases, symbols = _python_imports(text)
        return _prefix_matches(symbols, token)
    if language in ("c", "cpp"):
        return _prefix_matches(_c_imported_symbols(language, text), token)
    if language == "java":
        return _prefix_matches(_java_imported_symbols(text), token)
    if language in ("javascript", "typescript"):
        _aliases, symbols = _js_imports(text)
        return _prefix_matches(symbols, token)
    return []

# ---------------------------------------------------------------------------
# Context-aware candidates
# ---------------------------------------------------------------------------


def _python_context(
    text: str, before: str, token: str
) -> list[str] | None:
    aliases, _symbols = _python_imports(text)
    token_start = max(0, len(before) - len(token))
    prefix = before[:token_start]
    match = re.search(
        r"([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\.\s*$", prefix
    )
    if match:
        qualifier = match.group(1)
        module = aliases.get(qualifier, qualifier)
        if module in PYTHON_LIBRARIES:
            return _prefix_matches(PYTHON_LIBRARIES[module], token)
        root, _, rest = qualifier.partition(".")
        if root in aliases:
            module = aliases[root] + (f".{rest}" if rest else "")
            if module in PYTHON_LIBRARIES:
                return _prefix_matches(PYTHON_LIBRARIES[module], token)
        return []

    if before.lstrip().startswith("#"):
        return None

    match = re.match(r"^\s*from\s+([\w.]+)\s+import\b", before)
    if match:
        return _prefix_matches(PYTHON_LIBRARIES.get(match.group(1), ()), token)
    match = re.match(r"^\s*from\s+([\w.]*)$", before)
    if match:
        return _prefix_matches(python_module_names(), match.group(1))
    if re.match(r"^\s*import\s+", before) and not re.search(r"\bas\b", before):
        return _prefix_matches(python_module_names(), token)
    return None


def _c_context(language: str, text: str, before: str, token: str) -> list[str] | None:
    match = re.match(r'^\s*#\s*include\s*([<"])([^>"]*)$', before)
    if match:
        opener, prefix = match.group(1), match.group(2)
        if language == "c":
            header_names = C_HEADER_ORDER
        else:
            header_names = CPP_HEADER_ORDER + C_HEADER_ORDER
        closing = ">" if opener == "<" else '"'
        return [
            f"{header}{closing}"
            for header in _prefix_matches(
                header_names, prefix, allow_exact=True
            )
        ]
    if language == "cpp":
        token_start = max(0, len(before) - len(token))
        prefix = before[:token_start]
        if re.search(r"\bstd\s*::\s*$", prefix):
            return _prefix_matches(CPP_STD_SYMBOLS, token)
    return None


def _java_context(text: str, before: str, token: str) -> list[str] | None:
    if re.match(r"^\s*import\s+(?:static\s+)?", before):
        return _prefix_matches(JAVA_IMPORTS, token)
    return None


def _js_context(text: str, before: str, token: str) -> list[str] | None:
    for pattern in (
        r'\bfrom\s*([\'"])([^\'"]*)$',
        r'^\s*import\s*([\'"])([^\'"]*)$',
        r'\b(?:require|import)\s*\(\s*([\'"])([^\'"]*)$',
    ):
        match = re.search(pattern, before)
        if match:
            return _quoted(JS_MODULES, match.group(2), match.group(1))
    aliases, _symbols = _js_imports(text)
    token_start = max(0, len(before) - len(token))
    prefix = before[:token_start]
    match = re.search(r"([A-Za-z_$]\w*)\.\s*$", prefix)
    if match:
        package = aliases.get(match.group(1), match.group(1))
        symbols = _js_package_symbols(package)
        if symbols:
            return _prefix_matches(symbols, token)
        return []
    return None


def _go_context(
    text: str, before: str, token: str, line_index: int
) -> list[str] | None:
    match = re.match(r'^\s*import\s+(?:\w+\s+)?([\'"])([^\'"]*)$', before)
    if match:
        return _quoted(GO_IMPORT_PATHS, match.group(2), match.group(1))
    if _go_import_block_open(text, line_index):
        match = re.match(r'^\s*(?:\w+\s+)?([\'"])([^\'"]*)$', before)
        if match:
            return _quoted(GO_IMPORT_PATHS, match.group(2), match.group(1))
    token_start = max(0, len(before) - len(token))
    prefix = before[:token_start]
    match = re.search(r"([A-Za-z_]\w*)\.\s*$", prefix)
    if match:
        aliases = _go_aliases(text)
        package = aliases.get(match.group(1), match.group(1))
        symbols = GO_PACKAGES.get(package, ())
        if symbols:
            return _prefix_matches(symbols, token)
        return []
    return None


def _rust_paths_under(base: str) -> list[str]:
    prefix = f"{base}::"
    result: list[str] = []
    seen: set[str] = set()
    for path in RUST_USE_PATHS:
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix):]
        parts = relative.split("::")
        for index in range(1, len(parts) + 1):
            candidate = "::".join(parts[:index])
            if candidate in seen:
                continue
            seen.add(candidate)
            result.append(candidate)
    result.sort(key=lambda item: item.count("::"))
    return result


def _rust_qualifier(before: str, token: str) -> str | None:
    prefix_text = before[: max(0, len(before) - len(token))]
    match = re.search(
        r"((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)::\s*$",
        prefix_text,
    )
    return match.group(1) if match else None


def _rust_type_members(qualifier: str) -> tuple[str, ...] | None:
    members = RUST_TYPE_MEMBERS.get(qualifier)
    if members is None:
        members = RUST_TYPE_MEMBERS.get(qualifier.rsplit("::", 1)[-1])
    return members


def _rust_context(before: str, token: str) -> list[str] | None:
    parts = _rust_use_parts(before)
    if parts is not None:
        base, _item, brace_seen = parts
        prefix = token.strip()
        if brace_seen:
            base_text = "::".join(base)
            if not base_text:
                return []
            return _prefix_matches(_rust_paths_under(base_text), prefix)
        return _prefix_matches(RUST_USE_PATHS, prefix)

    qualifier = _rust_qualifier(before, token)
    if qualifier is None:
        return None
    prefix = token.strip()
    members = _rust_type_members(qualifier)
    if members:
        return _prefix_matches(members, prefix)
    if qualifier in ("std", "core", "alloc") or any(
        path.startswith(f"{qualifier}::") for path in RUST_USE_PATHS
    ):
        return _prefix_matches(_rust_paths_under(qualifier), prefix)
    return []


def _cs_context(before: str, token: str) -> list[str] | None:
    match = re.match(r"^\s*using\s+(?:static\s+)?([\w.]*)$", before)
    if match and match.group(1) != "var":
        return _prefix_matches(CS_NAMESPACES, token)
    return None


def _ruby_context(before: str) -> list[str] | None:
    match = re.search(r'\brequire\s*\(?\s*([\'"])([^\'"]*)$', before)
    if match:
        return _quoted(RUBY_REQUIRES, match.group(2), match.group(1))
    return None


def _lua_context(before: str) -> list[str] | None:
    match = re.search(r'\brequire\s*\(?\s*([\'"])([^\'"]*)$', before)
    if match:
        return _quoted(LUA_MODULES, match.group(2), match.group(1))
    return None


def _php_context(before: str, token: str) -> list[str] | None:
    if re.match(r"^\s*use\s+[\w\\]*$", before):
        return _prefix_matches(PHP_NAMESPACES, token)
    return None


def library_context_candidates(
    language: str,
    text: str,
    line: str,
    token: str,
    column: int,
    line_index: int = -1,
) -> list[str] | None:
    """Return candidates for an import/include context, or None."""
    before = line[:column]
    if language == "python":
        return _python_context(text, before, token)
    if language in ("c", "cpp"):
        return _c_context(language, text, before, token)
    if language == "java":
        return _java_context(text, before, token)
    if language in ("javascript", "typescript"):
        return _js_context(text, before, token)
    if language == "go":
        return _go_context(text, before, token, line_index)
    if language == "rust":
        return _rust_context(before, token)
    if language == "csharp":
        return _cs_context(before, token)
    if language == "ruby":
        return _ruby_context(before)
    if language == "lua":
        return _lua_context(before)
    if language == "php":
        return _php_context(before, token)
    return None

