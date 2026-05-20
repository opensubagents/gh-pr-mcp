# Managed Agents reference — section index

Generated outline of every H1/H2/H3 in the bundled `.md` files. Use this to locate the right file/section before opening it. For machine-readable line ranges, see `manifest.tsv`.

## `overview.md`
- # Claude Managed Agents overview  *(L1–L115)*
  - ## Core concepts  *(L26–L36)*
  - ## How it works  *(L37–L56)*
  - ## When to use Claude Managed Agents  *(L57–L65)*
  - ## Supported tools  *(L66–L76)*
  - ## Beta access  *(L77–L89)*
  - ## Rate limits  *(L90–L100)*
  - ## Branding guidelines  *(L101–L115)*

## `quickstart.md`
- # Get started with Claude Managed Agents  *(L1–L912)*
  - ## Core concepts  *(L13–L21)*
  - ## Prerequisites  *(L22–L26)*
  - ## Install the CLI  *(L27–L74)*
  - ## Install the SDK  *(L75–L120)*
  - ## Create your first session  *(L121–L886)*
  - ## What's happening  *(L887–L896)*
  - ## Next steps  *(L897–L912)*

## `onboarding.md`
- # Prototype in Console  *(L1–L125)*
  - ## How to build an agent  *(L13–L23)*
  - ## Testing an agent  *(L24–L27)*
  - ## From prototype to code  *(L28–L125)*

## `agent-setup.md`
- # Define your agent  *(L1–L481)*
  - ## Agent configuration fields  *(L15–L28)*
  - ## Create an agent  *(L29–L196)*
  - ## Update an agent  *(L197–L323)*
    - ### Update semantics  *(L310–L323)*
  - ## Agent lifecycle  *(L324–L476)*
    - ### List versions  *(L332–L407)*
    - ### Archive an agent  *(L408–L476)*
  - ## Next steps  *(L477–L481)*

## `define-outcomes.md`
- # Define outcomes  *(L1–L723)*
  - ## Create a rubric  *(L17–L143)*
  - ## Create a session with an outcome  *(L144–L386)*
  - ## Outcome events  *(L387–L470)*
    - ### Define outcome user event  *(L397–L412)*
    - ### Outcome evaluation start  *(L413–L426)*
    - ### Outcome evaluation ongoing  *(L427–L439)*
    - ### Outcome evaluation end  *(L440–L470)*
  - ## Checking on outcome status  *(L471–L567)*
  - ## Retrieving deliverables  *(L568–L723)*

## `tools.md`
- # Tools  *(L1–L462)*
  - ## Available tools  *(L15–L29)*
  - ## Configuring the toolset  *(L30–L214)*
    - ### Disabling specific tools  *(L185–L198)*
    - ### Enabling only specific tools  *(L199–L214)*
  - ## Custom tools  *(L215–L462)*
    - ### Best practices for custom tool definitions  *(L457–L462)*

## `skills.md`
- # Skills  *(L1–L189)*
  - ## Enable skills on a session  *(L20–L182)*
  - ## Skill types  *(L183–L189)*

## `mcp-connector.md`
- # MCP connector  *(L1–L343)*
  - ## Declare MCP servers on the agent  *(L20–L233)*
  - ## Provide auth at session creation  *(L234–L338)*
  - ## Supported MCP server types  *(L339–L343)*

## `multi-agent.md`
- # Multiagent sessions  *(L1–L1159)*
  - ## How it works  *(L13–L30)*
    - ### What to delegate  *(L21–L30)*
  - ## Configure the coordinator  *(L31–L245)*
  - ## Create the session  *(L246–L338)*
  - ## Threads  *(L339–L1159)*
    - ### Primary thread events  *(L735–L747)*
    - ### Session thread events  *(L748–L1014)*
    - ### Tool permissions and custom tools  *(L1015–L1159)*

## `sessions.md`
- # Start a session  *(L1–L608)*
  - ## Creating a session  *(L13–L185)*
  - ## MCP authentication through vaults  *(L186–L273)*
  - ## Starting the session  *(L274–L404)*
  - ## Session statuses  *(L405–L415)*
  - ## Other session operations  *(L416–L608)*
    - ### Retrieving a session  *(L418–L465)*
    - ### Listing sessions  *(L466–L521)*
    - ### Archiving a session  *(L522–L564)*
    - ### Deleting a session  *(L565–L608)*

## `events-and-streaming.md`
- # Session event stream  *(L1–L1798)*
  - ## Event types  *(L13–L80)*
  - ## Integrating events  *(L81–L1193)*
  - ## Additional scenarios  *(L1194–L1784)*
    - ### Handling custom tool calls  *(L1196–L1487)*
    - ### Tool confirmation  *(L1488–L1737)*
    - ### Resuming an idle session  *(L1738–L1765)*
    - ### Tracking usage  *(L1766–L1784)*
  - ## Console observability  *(L1785–L1792)*
  - ## Debugging tips  *(L1793–L1798)*

## `environments.md`
- # Cloud environment setup  *(L1–L669)*
  - ## Create an environment  *(L13–L138)*
  - ## Use the environment in a session  *(L139–L223)*
  - ## Configuration options  *(L224–L501)*
    - ### Packages  *(L226–L384)*
    - ### Networking  *(L385–L501)*
  - ## Environment lifecycle  *(L502–L508)*
  - ## Manage environments  *(L509–L666)*
  - ## Pre-installed runtimes  *(L667–L669)*

## `cloud-containers.md`
- # Container reference  *(L1–L71)*
  - ## Programming languages  *(L13–L25)*
  - ## Databases  *(L26–L37)*
  - ## Utilities  *(L38–L62)*
    - ### System tools  *(L40–L48)*
    - ### Development tools  *(L49–L56)*
    - ### Text processing  *(L57–L62)*
  - ## Container specifications  *(L63–L71)*

## `permission-policies.md`
- # Permission policies  *(L1–L877)*
  - ## Permission policy types  *(L13–L19)*
  - ## Set a policy for a toolset  *(L20–L431)*
    - ### Agent toolset permissions  *(L22–L188)*
    - ### MCP toolset permissions  *(L189–L431)*
  - ## Override an individual tool policy  *(L432–L612)*
  - ## Respond to confirmation requests  *(L613–L874)*
  - ## Custom tools  *(L875–L877)*

## `vaults.md`
- # Authenticate with vaults  *(L1–L850)*
  - ## Create a vault  *(L15–L133)*
  - ## Add a credential  *(L134–L518)*
  - ## Reference the vault at session creation  *(L519–L633)*
  - ## Credential refresh  *(L634–L695)*
    - ### Diagnose an OAuth refresh failure  *(L652–L695)*
  - ## Rotate a credential  *(L696–L844)*
  - ## Other operations  *(L845–L850)*

## `files.md`
- # Adding files  *(L1–L720)*
  - ## Uploading files  *(L13–L95)*
  - ## Mounting files in a session  *(L96–L259)*
  - ## Multiple files  *(L260–L352)*
  - ## Managing files on a running session  *(L353–L569)*
  - ## Listing and downloading session files  *(L570–L701)*
  - ## Supported file types  *(L702–L711)*
  - ## File paths  *(L712–L720)*

## `memory.md`
- # Using agent memory  *(L1–L1460)*
  - ## Overview  *(L13–L19)*
  - ## Create a memory store  *(L20–L221)*
    - ### Seed it with content (optional)  *(L126–L221)*
  - ## Attach a memory store to a session  *(L222–L406)*
    - ### How the agent accesses memory  *(L399–L406)*
  - ## View and edit memories  *(L407–L999)*
    - ### List memories  *(L411–L528)*
    - ### Read a memory  *(L529–L612)*
    - ### Create a memory  *(L613–L710)*
    - ### Update a memory  *(L711–L922)*
    - ### Delete a memory  *(L923–L999)*
  - ## Audit memory changes  *(L1000–L1310)*
    - ### List versions  *(L1010–L1137)*
    - ### Retrieve a version  *(L1138–L1225)*
    - ### Redact a version  *(L1226–L1310)*
  - ## Manage memory stores  *(L1311–L1457)*
    - ### List stores  *(L1315–L1395)*
    - ### Archive a store  *(L1396–L1457)*
  - ## Limits  *(L1458–L1460)*

## `github.md`
- # Accessing GitHub  *(L1–L915)*
  - ## GitHub MCP and Session Resources  *(L15–L402)*
  - ## Token permissions  *(L403–L417)*
  - ## Multiple repositories  *(L418–L590)*
  - ## Managing repositories on a running session  *(L591–L741)*
  - ## Creating pull requests  *(L742–L915)*

## `webhooks.md`
- # Subscribe to webhooks  *(L1–L366)*
  - ## Supported event types  *(L11–L38)*
  - ## Register an endpoint  *(L39–L48)*
  - ## Verify the signature  *(L49–L277)*
  - ## Handle an event  *(L278–L360)*
  - ## Delivery behavior  *(L361–L366)*

## `dreams.md`
- # Dreams  *(L1–L717)*
  - ## How it works  *(L21–L29)*
  - ## Create a dream  *(L30–L210)*
  - ## Track progress  *(L211–L317)*
    - ### Lifecycle  *(L304–L313)*
    - ### Watch the pipeline run  *(L314–L317)*
  - ## Use the output  *(L318–L494)*
  - ## Cancel a dream  *(L495–L552)*
  - ## Archive a dream  *(L553–L612)*
  - ## List dreams  *(L613–L691)*
  - ## Errors  *(L692–L704)*
  - ## Billing  *(L705–L708)*
  - ## Limits  *(L709–L717)*

