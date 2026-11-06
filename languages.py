"""Language registry: extensions, syntax specs and run metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Keyword / type lists
# ---------------------------------------------------------------------------

C_KEYWORDS = (
    "alignas|alignof|auto|bool|break|case|const|constexpr|continue|default|do|"
    "else|enum|extern|false|for|goto|if|inline|nullptr|register|restrict|return|"
    "sizeof|static|static_assert|struct|switch|thread_local|true|typedef|typeof|"
    "typeof_unqual|union|volatile|while|_Alignas|_Alignof|_Atomic|_BitInt|_Bool|"
    "_Complex|_Decimal32|_Decimal64|_Decimal128|_Generic|_Imaginary|_Noreturn|"
    "_Static_assert|_Thread_local"
)
C_TYPES = (
    "bool|char|char8_t|char16_t|char32_t|double|float|int|long|short|signed|"
    "unsigned|void|size_t|ssize_t|ptrdiff_t|intmax_t|uintmax_t|intptr_t|"
    "uintptr_t|wchar_t|int8_t|int16_t|int32_t|int64_t|uint8_t|uint16_t|uint32_t|"
    "uint64_t|int_least8_t|int_least16_t|int_least32_t|int_least64_t|"
    "uint_least8_t|uint_least16_t|uint_least32_t|uint_least64_t|int_fast8_t|"
    "int_fast16_t|int_fast32_t|int_fast64_t|uint_fast8_t|uint_fast16_t|"
    "uint_fast32_t|uint_fast64_t|FILE|va_list|time_t|clock_t|div_t|ldiv_t|"
    "lldiv_t|sig_atomic_t|max_align_t|off_t|pid_t"
)
C_CONSTANTS = "NULL|true|false|EOF|EXIT_SUCCESS|EXIT_FAILURE|RAND_MAX|SEEK_SET|SEEK_CUR|SEEK_END"
C_BUILTINS = (
    "printf|fprintf|sprintf|snprintf|vprintf|vfprintf|scanf|fscanf|sscanf|"
    "malloc|calloc|realloc|free|memcpy|memmove|memset|memcmp|strlen|strcpy|"
    "strncpy|strcat|strncat|strcmp|strncmp|strchr|strrchr|strstr|strtok|atoi|"
    "atol|atoll|atof|strtol|strtoul|strtod|exit|abort|atexit|assert|getchar|"
    "putchar|puts|gets|fgets|fputs|fopen|fclose|fread|fwrite|fseek|ftell|"
    "rewind|perror|qsort|bsearch|abs|labs|llabs|rand|srand|time|clock|difftime|"
    "mktime|localtime|gmtime|strftime|sqrt|pow|sin|cos|tan|log|exp|floor|ceil|"
    "round|fabs|isalpha|isdigit|isspace|isupper|islower|toupper|tolower"
)

CPP_KEYWORDS = (
    "alignas|alignof|and|and_eq|asm|auto|bitand|bitor|break|case|catch|class|"
    "compl|concept|const|consteval|constexpr|constinit|const_cast|continue|"
    "co_await|co_return|co_yield|decltype|default|delete|do|dynamic_cast|else|"
    "enum|explicit|export|extern|final|for|friend|goto|if|import|inline|module|"
    "mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|override|"
    "private|protected|public|register|reinterpret_cast|requires|return|sizeof|"
    "static|static_assert|static_cast|struct|switch|template|this|thread_local|"
    "throw|try|typedef|typeid|typename|union|using|virtual|volatile|while|xor|xor_eq"
)
CPP_TYPES = (
    "bool|char|char8_t|char16_t|char32_t|double|float|int|long|short|signed|"
    "unsigned|void|wchar_t|size_t|ptrdiff_t|std|string|string_view|vector|array|"
    "deque|list|forward_list|map|unordered_map|multimap|unordered_multimap|set|"
    "unordered_set|multiset|unordered_multiset|stack|queue|priority_queue|pair|"
    "tuple|optional|variant|any|span|bitset|function|thread|mutex|atomic|"
    "shared_ptr|unique_ptr|weak_ptr|make_shared|make_unique|filesystem|chrono|"
    "ranges|format|expected|byte|int8_t|int16_t|int32_t|int64_t|uint8_t|uint16_t|"
    "uint32_t|uint64_t|intptr_t|uintptr_t|intmax_t|uintmax_t"
)
CPP_CONSTANTS = "true|false|nullptr|NULL|EOF|std"
CPP_BUILTINS = (
    "cout|cin|cerr|clog|endl|flush|setw|setprecision|make_pair|make_shared|"
    "make_unique|move|forward|swap|sort|stable_sort|find|find_if|reverse|"
    "accumulate|begin|end|size|empty|push_back|emplace_back|insert|erase|clear|"
    "at|front|back|reserve|resize|to_string|stoi|stol|stod|getline"
)

JAVA_KEYWORDS = (
    "abstract|assert|break|case|catch|class|const|continue|default|do|else|enum|"
    "exports|extends|final|finally|for|goto|if|implements|import|instanceof|"
    "interface|module|native|new|non-sealed|open|opens|package|permits|private|"
    "protected|provides|public|record|requires|return|sealed|static|strictfp|"
    "super|switch|synchronized|this|throw|throws|to|transient|transitive|try|"
    "uses|var|volatile|while|with|yield"
)
JAVA_TYPES = (
    "boolean|byte|char|double|float|int|long|short|void|String|Object|Integer|"
    "Long|Double|Float|Boolean|Character|Byte|Short|Number|BigInteger|BigDecimal|"
    "List|ArrayList|LinkedList|Map|HashMap|LinkedHashMap|TreeMap|Set|HashSet|"
    "LinkedHashSet|TreeSet|Collection|Arrays|Collections|Optional|Stream|IntStream|"
    "LongStream|DoubleStream|Collectors|System|Math|Thread|Runnable|Exception|"
    "RuntimeException|Error|Throwable|Class|StringBuilder|StringBuffer|Scanner|"
    "File|Path|Files|InputStream|OutputStream|Reader|Writer|BufferedReader|"
    "BufferedWriter|FileReader|FileWriter|PrintWriter|Socket|ServerSocket|UUID|"
    "Pattern|Matcher|LocalDate|LocalTime|LocalDateTime|ZonedDateTime|Instant|"
    "Duration|Period|ExecutorService|Executors|Future|CompletableFuture|Supplier|"
    "Consumer|Function|Predicate|BiFunction|UnaryOperator|BinaryOperator"
)
JAVA_CONSTANTS = "true|false|null|this|super"

JS_KEYWORDS = (
    "as|async|await|break|case|catch|class|const|continue|debugger|default|delete|"
    "do|else|export|extends|finally|for|from|function|get|if|implements|import|in|"
    "instanceof|interface|let|new|of|package|private|protected|public|return|set|"
    "static|super|switch|this|throw|try|typeof|var|void|while|with|yield|enum|"
    "declare|abstract|readonly|namespace|module|type|keyof|infer|is|asserts|"
    "satisfies|override|accessor|using"
)
JS_TYPES = (
    "any|boolean|number|string|symbol|unknown|never|object|bigint|undefined|"
    "void|Array|Promise|Map|Set|WeakMap|WeakSet|Date|RegExp|Error|Function|"
    "Object|String|Number|Boolean|Symbol|BigInt|Uint8Array|JSON"
)
JS_CONSTANTS = "true|false|null|undefined|NaN|Infinity"
JS_BUILTINS = (
    "console|document|window|globalThis|process|require|module|exports|Math|"
    "JSON|Reflect|Proxy|Intl|Atomics|WebAssembly|ArrayBuffer|SharedArrayBuffer|"
    "DataView|Int8Array|Uint8Array|Uint8ClampedArray|Int16Array|Uint16Array|"
    "Int32Array|Uint32Array|Float32Array|Float64Array|BigInt64Array|"
    "BigUint64Array|Map|Set|WeakMap|WeakSet|Date|RegExp|Error|TypeError|"
    "RangeError|SyntaxError|ReferenceError|EvalError|URIError|AggregateError|"
    "Promise|Symbol|BigInt|URL|URLSearchParams|FormData|Headers|Request|Response|"
    "Blob|File|TextEncoder|TextDecoder|AbortController|AbortSignal|Event|EventTarget|"
    "WebSocket|Worker|EventSource|crypto|performance|navigator|localStorage|"
    "sessionStorage|location|history|alert|confirm|prompt|requestAnimationFrame|"
    "cancelAnimationFrame|setTimeout|setInterval|clearTimeout|clearInterval|fetch|"
    "structuredClone|queueMicrotask|parseInt|parseFloat|isNaN|isFinite|"
    "encodeURIComponent|decodeURIComponent"
)

RUST_KEYWORDS = (
    "as|async|await|break|const|continue|crate|dyn|else|enum|extern|false|fn|for|"
    "if|impl|in|let|loop|match|mod|move|mut|pub|ref|return|self|Self|static|"
    "struct|super|trait|true|type|unsafe|use|where|while|yield|union|macro_rules"
)
RUST_TYPES = (
    "bool|char|str|String|i8|i16|i32|i64|i128|isize|u8|u16|u32|u64|u128|usize|"
    "f32|f64|Vec|VecDeque|Option|Result|Box|Rc|Arc|RefCell|Cell|Mutex|RwLock|"
    "HashMap|HashSet|BTreeMap|BTreeSet|BinaryHeap|LinkedList|Cow|Path|PathBuf|"
    "OsStr|OsString|CString|CStr|Duration|Instant|SystemTime|PhantomData|Pin|"
    "Range|RangeInclusive|RangeFrom|RangeTo|RangeFull|NonZeroUsize|NonZeroU32|"
    "AtomicBool|AtomicIsize|AtomicUsize|AtomicI32|AtomicU32|AtomicI64|AtomicU64"
)
RUST_CONSTANTS = "true|false|None|Some|Ok|Err|Ordering"

GO_KEYWORDS = (
    "break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|"
    "goto|if|import|interface|map|package|range|return|select|struct|switch|type|var"
)
GO_TYPES = (
    "bool|byte|complex64|complex128|error|float32|float64|int|int8|int16|int32|"
    "int64|rune|string|uint|uint8|uint16|uint32|uint64|uintptr|any"
)
GO_BUILTINS = (
    "append|cap|clear|close|complex|copy|delete|imag|len|make|max|min|new|panic|"
    "print|println|real|recover"
)
GO_CONSTANTS = "true|false|nil|iota"

BASH_KEYWORDS = (
    "if|then|else|elif|fi|for|while|until|do|done|case|esac|function|in|select|"
    "time|coproc|return|exit|break|continue|local|export|readonly|declare|typeset|"
    "unset|shift|source|alias|eval|exec|trap|wait|set|shopt|getopts"
)
BASH_BUILTINS = (
    "echo|printf|cd|pwd|read|mapfile|readarray|test|let|kill|jobs|bg|fg|disown|"
    "type|command|builtin|enable|help|umask|ulimit|history|hash|dirs|pushd|popd|"
    "caller|bind|complete|compgen|compopt|times|suspend|logout|wait|trap"
)
BASH_CONSTANTS = "true|false"

PERL_KEYWORDS = (
    "my|our|local|sub|if|elsif|else|unless|while|until|for|foreach|do|last|next|"
    "redo|return|package|use|require|no|BEGIN|END|and|or|not|xor|eq|ne|lt|gt|le|"
    "ge|cmp|given|when|default|state|say|die|warn|eval|print|printf"
)
PERL_BUILTINS = (
    "chomp|chop|split|join|push|pop|shift|unshift|keys|values|each|exists|delete|"
    "sort|reverse|map|grep|scalar|ref|bless|open|close|read|write|length|substr|"
    "index|sprintf|defined|undef|wantarray|caller"
)
PERL_CONSTANTS = "undef|__FILE__|__LINE__|__PACKAGE__"

LUA_KEYWORDS = (
    "and|break|do|else|elseif|end|false|for|function|goto|if|in|local|nil|not|"
    "or|repeat|return|then|true|until|while"
)
LUA_BUILTINS = (
    "print|warn|pairs|ipairs|next|select|type|tostring|tonumber|rawget|rawset|"
    "rawequal|rawlen|setmetatable|getmetatable|assert|error|pcall|xpcall|load|"
    "loadfile|dofile|require|collectgarbage|string|table|math|io|os|coroutine|"
    "utf8|debug|package|bit32"
)
LUA_CONSTANTS = "true|false|nil|_G|_VERSION"

RUBY_KEYWORDS = (
    "alias|and|begin|break|case|class|def|defined|do|else|elsif|end|ensure|false|"
    "for|if|in|module|next|nil|not|or|redo|rescue|retry|return|self|super|then|"
    "true|undef|unless|until|when|while|yield|require|require_relative|include|"
    "extend|attr_accessor|attr_reader|attr_writer|private|protected|public|new|"
    "raise|puts|print|p|loop|lambda|proc"
)
RUBY_BUILTINS = (
    "Array|Hash|String|Integer|Float|Symbol|Proc|Range|Regexp|Time|Date|DateTime|"
    "File|Dir|IO|Kernel|Object|Class|Module|Struct|Enumerable|Math|JSON|YAML|"
    "Marshal|SecureRandom|OpenStruct|Pathname|Set|Method|UnboundMethod|Thread|"
    "ThreadGroup|Queue|Mutex|ConditionVariable|Exception|StandardError"
)
RUBY_CONSTANTS = "true|false|nil|__FILE__|__LINE__|__dir__"

PHP_KEYWORDS = (
    "abstract|and|array|as|break|callable|case|catch|class|clone|const|continue|"
    "declare|default|do|echo|else|elseif|empty|enddeclare|endfor|endforeach|endif|"
    "endswitch|endwhile|enum|eval|exit|extends|final|finally|fn|for|foreach|"
    "function|global|goto|if|implements|include|include_once|instanceof|insteadof|"
    "interface|isset|list|match|namespace|new|or|print|private|protected|public|"
    "readonly|require|require_once|return|static|switch|throw|trait|try|unset|use|"
    "var|while|xor|yield|true|false|null"
)
PHP_TYPES = (
    "bool|boolean|int|integer|float|double|string|array|object|mixed|void|never|"
    "iterable|callable|self|parent|static|Closure|Generator|Exception|Throwable"
)
PHP_BUILTINS = (
    "strlen|str_replace|str_contains|str_starts_with|str_ends_with|explode|implode|"
    "trim|ltrim|rtrim|substr|substr_count|str_pad|str_repeat|strtolower|strtoupper|"
    "ucfirst|lcfirst|sprintf|printf|print_r|var_dump|count|array_map|array_filter|"
    "array_merge|array_keys|array_values|array_slice|array_splice|array_reverse|"
    "array_unique|array_search|array_key_exists|array_push|array_pop|array_shift|"
    "array_unshift|sort|rsort|usort|ksort|asort|in_array|json_encode|json_decode|"
    "json_last_error|is_array|is_string|is_numeric|is_int|is_bool|is_null|is_object|"
    "is_callable|intval|floatval|strval|boolval|gettype|settype|serialize|"
    "unserialize|file_get_contents|file_put_contents|fopen|fclose|fgets|fwrite|"
    "preg_match|preg_replace|preg_split|md5|sha1|password_hash|password_verify"
)

SQL_KEYWORDS = (
    "add|all|alter|analyze|and|any|as|asc|attach|backup|begin|between|by|case|"
    "check|column|commit|conflict|constraint|create|cross|database|default|delete|"
    "desc|detach|distinct|do|drop|else|end|except|exec|exists|explain|fetch|"
    "foreign|from|full|group|having|if|in|index|inner|insert|intersect|into|is|"
    "join|key|left|like|limit|merge|natural|not|nothing|null|offset|on|or|order|"
    "outer|over|partition|pragma|primary|procedure|references|replace|returning|"
    "right|rollback|rownum|select|set|table|then|top|transaction|trigger|truncate|"
    "union|unique|update|using|vacuum|values|view|when|where|window|with"
)
SQL_TYPES = (
    "bigint|bigserial|binary|bit|blob|boolean|bytea|char|cidr|date|datetime|decimal|"
    "double|enum|float|inet|int|integer|json|jsonb|longtext|macaddr|money|numeric|"
    "real|serial|smallint|smallserial|text|time|timestamp|tinyint|uuid|varbinary|"
    "varchar|nvarchar|xml|array"
)
SQL_CONSTANTS = "true|false|null|current_date|current_time|current_timestamp"

CS_KEYWORDS = (
    "abstract|as|async|await|base|break|case|catch|checked|class|const|continue|"
    "default|delegate|do|else|enum|event|explicit|extern|finally|fixed|for|foreach|"
    "get|goto|if|implicit|in|init|interface|internal|is|lock|namespace|new|"
    "operator|out|override|params|partial|private|protected|public|readonly|record|"
    "ref|required|return|sealed|set|sizeof|stackalloc|static|struct|switch|this|"
    "throw|try|typeof|unchecked|unsafe|using|var|virtual|volatile|when|where|while|"
    "yield|global|file|with"
)
CS_TYPES = (
    "bool|byte|sbyte|char|decimal|double|float|int|uint|long|ulong|short|ushort|"
    "object|string|void|dynamic|nint|nuint|DateTime|DateTimeOffset|TimeSpan|Guid|"
    "Uri|Task|ValueTask|List|Dictionary|HashSet|Queue|Stack|LinkedList|"
    "IEnumerable|ICollection|IList|IDictionary|IReadOnlyList|IReadOnlyDictionary|"
    "ImmutableArray|ImmutableList|Span|Memory|ReadOnlySpan|ReadOnlyMemory|"
    "StringBuilder|Nullable|Regex|Stream|File|Directory|Path|Console|Math"
)
CS_CONSTANTS = "true|false|null"

HTML_TAGS = (
    "a|abbr|address|area|article|aside|audio|b|base|bdi|bdo|blockquote|body|"
    "br|button|canvas|caption|cite|code|col|colgroup|data|datalist|dd|del|"
    "details|dfn|dialog|div|dl|dt|em|embed|fieldset|figcaption|figure|footer|"
    "form|h1|h2|h3|h4|h5|h6|head|header|hgroup|hr|html|i|iframe|img|input|ins|"
    "kbd|label|legend|li|link|main|map|mark|menu|meta|meter|nav|noscript|object|"
    "ol|optgroup|option|output|p|picture|pre|progress|q|rp|rt|ruby|s|samp|script|"
    "search|section|select|slot|small|source|span|strong|style|sub|summary|sup|"
    "table|tbody|td|template|textarea|tfoot|th|thead|time|title|tr|track|u|ul|"
    "var|video|wbr"
)
HTML_ATTRIBUTES = (
    "accept|accept-charset|accesskey|action|allow|alt|as|async|autocomplete|"
    "autofocus|autoplay|charset|checked|cite|class|cols|colspan|content|"
    "contenteditable|controls|coords|crossorigin|data|datetime|decoding|default|"
    "defer|dir|dirname|disabled|download|draggable|enctype|enterkeyhint|for|form|"
    "formaction|formenctype|formmethod|formnovalidate|formtarget|headers|height|"
    "hidden|high|href|hreflang|http-equiv|id|integrity|ismap|kind|label|lang|list|"
    "loading|loop|low|max|maxlength|media|method|min|minlength|multiple|muted|"
    "name|novalidate|open|optimum|pattern|placeholder|playsinline|poster|preload|"
    "readonly|referrerpolicy|rel|required|reversed|role|rows|rowspan|sandbox|"
    "scope|selected|shape|size|sizes|slot|span|spellcheck|src|srcdoc|srcset|start|"
    "step|style|tabindex|target|title|translate|type|usemap|value|width|wrap|"
    "aria-label|aria-hidden|aria-describedby|aria-expanded|aria-controls"
)
CSS_PROPERTIES = (
    "accent-color|align-content|align-items|align-self|all|animation|"
    "animation-delay|animation-direction|animation-duration|animation-fill-mode|"
    "animation-iteration-count|animation-name|animation-play-state|"
    "animation-timing-function|appearance|aspect-ratio|backdrop-filter|"
    "backface-visibility|background|background-attachment|background-blend-mode|"
    "background-clip|background-color|background-image|background-origin|"
    "background-position|background-repeat|background-size|block-size|border|"
    "border-block|border-bottom|border-bottom-color|border-bottom-left-radius|"
    "border-bottom-right-radius|border-bottom-style|border-bottom-width|"
    "border-collapse|border-color|border-image|border-inline|border-left|"
    "border-left-color|border-left-style|border-left-width|border-radius|"
    "border-right|border-right-color|border-right-style|border-right-width|"
    "border-spacing|border-style|border-top|border-top-color|"
    "border-top-left-radius|border-top-right-radius|border-top-style|"
    "border-top-width|border-width|bottom|box-shadow|box-sizing|break-after|"
    "break-before|break-inside|caption-side|caret-color|clear|clip|clip-path|"
    "color|column-count|column-gap|column-rule|column-width|columns|contain|"
    "content|counter-increment|counter-reset|cursor|direction|display|"
    "empty-cells|filter|flex|flex-basis|flex-direction|flex-flow|flex-grow|"
    "flex-shrink|flex-wrap|float|font|font-family|font-feature-settings|"
    "font-kerning|font-size|font-stretch|font-style|font-variant|font-weight|gap|"
    "grid|grid-area|grid-auto-columns|grid-auto-flow|grid-auto-rows|grid-column|"
    "grid-column-end|grid-column-gap|grid-column-start|grid-gap|grid-row|"
    "grid-row-end|grid-row-gap|grid-row-start|grid-template|grid-template-areas|"
    "grid-template-columns|grid-template-rows|height|hyphens|inline-size|inset|"
    "isolation|justify-content|justify-items|justify-self|left|letter-spacing|"
    "line-break|line-height|list-style|list-style-image|list-style-position|"
    "list-style-type|margin|margin-block|margin-bottom|margin-inline|margin-left|"
    "margin-right|margin-top|mask|max-block-size|max-height|max-inline-size|"
    "max-width|min-block-size|min-height|min-inline-size|min-width|mix-blend-mode|"
    "object-fit|object-position|opacity|order|outline|outline-color|outline-offset|"
    "outline-style|outline-width|overflow|overflow-wrap|overflow-x|overflow-y|"
    "overscroll-behavior|padding|padding-block|padding-bottom|padding-inline|"
    "padding-left|padding-right|padding-top|page-break-after|page-break-before|"
    "page-break-inside|perspective|perspective-origin|place-content|place-items|"
    "place-self|pointer-events|position|quotes|resize|right|rotate|row-gap|scale|"
    "scroll-behavior|tab-size|table-layout|text-align|text-align-last|"
    "text-decoration|text-decoration-color|text-decoration-line|"
    "text-decoration-style|text-indent|text-justify|text-overflow|text-shadow|"
    "text-transform|text-underline-offset|top|transform|transform-origin|"
    "transform-style|transition|transition-delay|transition-duration|"
    "transition-property|transition-timing-function|translate|unicode-bidi|"
    "user-select|vertical-align|visibility|white-space|width|will-change|"
    "word-break|word-spacing|word-wrap|writing-mode|z-index"
)
CSS_VALUES = (
    "absolute|auto|baseline|block|bold|border-box|both|center|column|contain|"
    "cover|currentColor|dashed|dotted|double|ease|ease-in|ease-in-out|ease-out|"
    "fixed|flex|flex-end|flex-start|grid|hidden|inherit|initial|inline|"
    "inline-block|inline-flex|italic|justify|left|line-through|lowercase|"
    "monospace|none|normal|nowrap|pointer|relative|repeat|right|solid|"
    "space-between|start|sticky|stretch|transparent|uppercase|visible|wrap"
)

# ---------------------------------------------------------------------------
# Language model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Language:
    key: str
    name: str
    extensions: tuple[str, ...]
    color: str
    highlighter: str | None = None
    line_comments: tuple[str, ...] = ()
    block_comment: tuple[str, str] | None = None
    keywords: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    builtins: tuple[str, ...] = ()
    constants: tuple[str, ...] = ()
    extra_rules: tuple[tuple, ...] = ()
    post_rules: tuple[tuple[str, str], ...] = ()
    string_quotes: tuple[str, ...] = ('"', "'")
    triple_strings: bool = False
    preprocessor: bool = False
    case_insensitive: bool = False
    template_strings: bool = False
    runner: str | None = None
    compiled: bool = False
    tools: tuple[str, ...] = ()
    aliases: tuple[str, ...] = field(default_factory=tuple)

    @property
    def comment(self) -> str:
        return self.line_comments[0] if self.line_comments else ""


def _exts(*values: str) -> tuple[str, ...]:
    return tuple(values)


LANGUAGES: dict[str, Language] = {}


def _register(language: Language) -> Language:
    LANGUAGES[language.key] = language
    return language


_register(
    Language(
        "python", "Python", _exts(".py", ".pyw", ".pyi"), "#6cc6ff",
        highlighter="python", line_comments=("#",),
        triple_strings=True, runner="python", tools=("python",),
        keywords=(
            "False|None|True|and|as|assert|async|await|break|case|class|continue|"
            "def|del|elif|else|except|finally|for|from|global|if|import|in|is|"
            "lambda|match|nonlocal|not|or|pass|raise|return|try|while|with|yield"
        ),
        builtins=(
            "abs|aiter|all|anext|any|ascii|bin|bool|breakpoint|bytearray|bytes|"
            "callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|"
            "enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|"
            "hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|"
            "list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|"
            "print|property|range|repr|reversed|round|set|setattr|slice|sorted|"
            "staticmethod|str|sum|super|tuple|type|vars|zip|__import__|BaseException|"
            "Exception|ArithmeticError|AssertionError|AttributeError|BufferError|"
            "EOFError|ImportError|ModuleNotFoundError|LookupError|MemoryError|"
            "NameError|NotImplementedError|OSError|FileNotFoundError|OverflowError|"
            "RecursionError|ReferenceError|RuntimeError|StopAsyncIteration|"
            "StopIteration|SyntaxError|IndentationError|TabError|SystemError|"
            "SystemExit|TypeError|UnboundLocalError|UnicodeError|UnicodeDecodeError|"
            "UnicodeEncodeError|UnicodeTranslateError|ValueError|ZeroDivisionError|"
            "KeyboardInterrupt|GeneratorExit|Warning|DeprecationWarning|"
            "PendingDeprecationWarning|RuntimeWarning|SyntaxWarning|UserWarning|"
            "FutureWarning|ImportWarning|UnicodeWarning|BytesWarning|ResourceWarning|"
            "ExceptionGroup|BaseExceptionGroup"
        ),
    )
)

_register(
    Language(
        "c", "C", _exts(".c", ".h"), "#8fd3ff",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"), preprocessor=True,
        keywords=C_KEYWORDS,
        types=C_TYPES,
        builtins=C_BUILTINS,
        constants=C_CONSTANTS,
        extra_rules=((r"#include\s*([<\"][^>\"]+[>\"])", "string", 1),),
        runner="c", compiled=True, tools=("gcc", "cc", "clang"),
    )
)

_register(
    Language(
        "cpp", "C++", _exts(".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"), "#7ea6ff",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"), preprocessor=True,
        keywords=CPP_KEYWORDS,
        types=CPP_TYPES,
        builtins=CPP_BUILTINS,
        constants=CPP_CONSTANTS,
        extra_rules=(
            (r"\bstd::[A-Za-z_]\w*", "type"),
            (r"#include\s*([<\"][^>\"]+[>\"])", "string", 1),
        ),
        runner="cpp", compiled=True, tools=("g++", "clang++", "c++"),
    )
)

_register(
    Language(
        "java", "Java", _exts(".java"), "#ffb86b",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=JAVA_KEYWORDS,
        types=JAVA_TYPES,
        constants=JAVA_CONSTANTS,
        extra_rules=((r"@[A-Za-z_]\w*", "decorator"),),
        runner="java", compiled=True, tools=("javac", "java"),
    )
)

_register(
    Language(
        "javascript", "JavaScript", _exts(".js", ".mjs", ".cjs"), "#ffd479",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=JS_KEYWORDS,
        types=JS_TYPES,
        constants=JS_CONSTANTS,
        builtins=JS_BUILTINS,
        extra_rules=((r"@[A-Za-z_]\w*", "decorator"),),
        string_quotes=('"', "'", "`"),
        runner="node", tools=("node",),
    )
)

_register(
    Language(
        "typescript", "TypeScript", _exts(".ts", ".mts", ".cts"), "#6cb6ff",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=JS_KEYWORDS,
        types=JS_TYPES,
        constants=JS_CONSTANTS,
        builtins=JS_BUILTINS,
        extra_rules=((r"@[A-Za-z_]\w*", "decorator"),),
        string_quotes=('"', "'", "`"),
        runner="node", tools=("node",),
    )
)

_register(
    Language(
        "rust", "Rust", _exts(".rs"), "#ff9e64",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=RUST_KEYWORDS,
        types=RUST_TYPES,
        constants=RUST_CONSTANTS,
        extra_rules=(
            (r"#!?\[[^\]]*\]", "decorator"),
            (r"\b[A-Za-z_]\w*!", "builtin"),
        ),
        string_quotes=('"',),
        runner="rust", compiled=True, tools=("rustc",),
    )
)

_register(
    Language(
        "go", "Go", _exts(".go"), "#63e6e2",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=GO_KEYWORDS,
        types=GO_TYPES,
        builtins=GO_BUILTINS,
        constants=GO_CONSTANTS,
        string_quotes=('"', "`"),
        runner="go", compiled=True, tools=("go",),
    )
)

_register(
    Language(
        "bash", "Shell", _exts(".sh", ".bash", ".zsh"), "#a6e3a1",
        highlighter="generic", line_comments=("#",),
        keywords=BASH_KEYWORDS,
        builtins=BASH_BUILTINS,
        constants=BASH_CONSTANTS,
        extra_rules=(
            (r"\$\{[^}]+\}|\$[A-Za-z_]\w*|\$[0-9@#?$*!-]", "variable"),
            (r"\b(?:if|then|fi|for|do|done|case|esac)\b", "keyword"),
        ),
        runner="bash", tools=("bash",),
    )
)

_register(
    Language(
        "perl", "Perl", _exts(".pl", ".pm"), "#8fd3ff",
        highlighter="generic", line_comments=("#",),
        keywords=PERL_KEYWORDS,
        builtins=PERL_BUILTINS,
        constants=PERL_CONSTANTS,
        extra_rules=(
            (r"[$@%][A-Za-z_]\w*|[$@%]\W", "variable"),
            (r"\b[A-Z][A-Za-z0-9_]*\b", "type"),
        ),
        string_quotes=('"', "'", "`"),
        runner="perl", tools=("perl",),
    )
)

_register(
    Language(
        "lua", "Lua", _exts(".lua"), "#7f8cff",
        highlighter="generic", line_comments=("--",),
        block_comment=("--[[", "]]"),
        keywords=LUA_KEYWORDS,
        builtins=LUA_BUILTINS,
        constants=LUA_CONSTANTS,
        extra_rules=((r"\.\.\.", "constant"),),
        runner="lua", tools=("lua", "luajit"),
    )
)

_register(
    Language(
        "ruby", "Ruby", _exts(".rb"), "#ff6b6b",
        highlighter="generic", line_comments=("#",),
        block_comment=("=begin", "=end"),
        keywords=RUBY_KEYWORDS,
        builtins=RUBY_BUILTINS,
        constants=RUBY_CONSTANTS,
        extra_rules=(
            (r"@@?[A-Za-z_]\w*|\$[A-Za-z_]\w*", "variable"),
            (r"(?<!:)\b:[A-Za-z_]\w*", "constant"),
        ),
        string_quotes=('"', "'", "`"),
        runner="ruby", tools=("ruby",),
    )
)

_register(
    Language(
        "php", "PHP", _exts(".php"), "#c8a6ff",
        highlighter="generic", line_comments=("//", "#"),
        block_comment=("/*", "*/"),
        keywords=PHP_KEYWORDS,
        types=PHP_TYPES,
        builtins=PHP_BUILTINS,
        extra_rules=((r"\$[A-Za-z_]\w*", "variable"),),
        runner="php", tools=("php",),
    )
)

_register(
    Language(
        "html", "HTML", _exts(".html", ".htm"), "#ff8a65",
        highlighter="markup", block_comment=("<!--", "-->"),
        builtins=HTML_TAGS + HTML_ATTRIBUTES,
    )
)

_register(
    Language(
        "xml", "XML", _exts(".xml", ".svg", ".xhtml"), "#ffb86b",
        highlighter="markup", block_comment=("<!--", "-->"),
        builtins=HTML_TAGS + HTML_ATTRIBUTES,
    )
)

_register(
    Language(
        "css", "CSS", _exts(".css"), "#6cb6ff",
        highlighter="css", block_comment=("/*", "*/"),
        builtins=CSS_PROPERTIES + CSS_VALUES,
    )
)

_register(
    Language(
        "json", "JSON", _exts(".json", ".jsonc"), "#ffd479",
        highlighter="generic", constants=("true|false|null",),
        string_quotes=('"',),
        post_rules=((r'"(?:\\.|[^"\\])*"(?=\s*:)', "key"),),
    )
)

_register(
    Language(
        "yaml", "YAML", _exts(".yml", ".yaml"), "#ff8ac2",
        highlighter="generic", line_comments=("#",),
        constants=("true|false|null|yes|no|on|off",),
        extra_rules=(
            (r"&[A-Za-z_]\w*|\*[A-Za-z_]\w*", "variable"),
            (r"!!?[A-Za-z_][\w/:.-]*", "decorator"),
        ),
        post_rules=((r"^\s*[\w./-]+(?=\s*:)", "key"),),
    )
)

_register(
    Language(
        "toml", "TOML", _exts(".toml"), "#ffb86b",
        highlighter="generic", line_comments=("#",),
        constants=("true|false",),
        extra_rules=((r"^\s*\[[^\]]+\]", "tag"),),
        post_rules=((r"^\s*[\w.-]+(?=\s*=)", "key"),),
    )
)

_register(
    Language(
        "markdown", "Markdown", _exts(".md", ".markdown"), "#c8a6ff",
        highlighter="markdown",
    )
)

_register(
    Language(
        "sql", "SQL", _exts(".sql"), "#63e6e2",
        highlighter="generic", line_comments=("--",),
        block_comment=("/*", "*/"), case_insensitive=True,
        keywords=SQL_KEYWORDS,
        types=SQL_TYPES,
        constants=SQL_CONSTANTS,
    )
)

_register(
    Language(
        "csharp", "C#", _exts(".cs"), "#c8a6ff",
        highlighter="generic", line_comments=("//",),
        block_comment=("/*", "*/"),
        keywords=CS_KEYWORDS,
        types=CS_TYPES,
        constants=CS_CONSTANTS,
        extra_rules=((r"\[[A-Za-z_][\w.]*(?:\([^)]*\))?\]", "decorator"),),
    )
)

_register(
    Language(
        "text", "Plain Text", _exts(), "#8b8ba7",
    )
)

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

EXTENSION_MAP: dict[str, Language] = {}
for _language in LANGUAGES.values():
    for _extension in _language.extensions:
        EXTENSION_MAP.setdefault(_extension.lower(), _language)


def language_for_key(key: str) -> Language:
    return LANGUAGES.get(key, LANGUAGES["text"])


def language_for_path(path: Path | None) -> Language:
    if path is None:
        return LANGUAGES["text"]
    return EXTENSION_MAP.get(path.suffix.lower(), LANGUAGES["text"])


def runnable_languages() -> list[Language]:
    return [lang for lang in LANGUAGES.values() if lang.runner]


def compiled_languages() -> list[Language]:
    return [lang for lang in LANGUAGES.values() if lang.compiled]


def display_languages() -> list[Language]:
    return [lang for lang in LANGUAGES.values() if lang.key != "text"]
