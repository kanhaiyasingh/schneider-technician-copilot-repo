# Azure components — provisioning guide

> **Audience:** the person who prepares the Azure environment **before** the
> workshop (facilitator, cloud admin, or a self-service participant with an
> Azure subscription). Participants who are handed a ready-made project can skip
> to [`setup.md`](./setup.md).

This workshop runs entirely on **Entra ID (Azure AD) authentication** — no API
keys. Everything you deploy here is referenced from `.env`
(see [`../.env.sample`](../.env.sample) and [`setup.md`](./setup.md)).

You will provision, in order:

1. A **Microsoft Foundry** resource + **project**
2. Two **model deployments** — a chat model and an embedding model
3. An **Azure AI Search** service (grounding for Labs 04–06)
4. An **Application Insights** resource (observability for Lab 06)
5. The **RBAC role assignments** that make keyless auth work

If you are also running the **advanced labs (07–09)** you additionally need a
small **`gpt-4.1-mini`** deployment and two extra RBAC roles — see
[§7 Advanced labs](#7-advanced-labs-0709--extra-prerequisites).

Estimated time: **20–30 minutes**. Estimated cost for a half-day workshop:
low tens of USD (mostly model tokens + the Search service tier).

---

## 0. Prerequisites

- An Azure subscription where you can **create resources** and **assign roles**
  (Owner or User Access Administrator on the target resource group).
- **Azure CLI** installed and signed in:
  ```bash
  az login
  az account set --subscription "<your-subscription-id>"
  ```
- A region that offers the models you need. This workshop was validated in a
  Foundry project with **`gpt-5.4`** (chat) and **`text-embedding-3-large`**
  (embeddings). Check model/region availability in the Foundry portal before you
  pick a region.

Set a few shell variables to reuse below (bash / PowerShell shown):

```bash
# bash
RG=schneider-workshop-rg
LOCATION=swedencentral
FOUNDRY=schneider-foundry           # Foundry (AI account) resource name
PROJECT=technician-copilot          # Foundry project name
SEARCH=schneider-workshop-search    # Azure AI Search service name
APPINSIGHTS=schneider-workshop-ai   # Application Insights name
```

```powershell
# PowerShell
$RG="schneider-workshop-rg"; $LOCATION="swedencentral"
$FOUNDRY="schneider-foundry"; $PROJECT="technician-copilot"
$SEARCH="schneider-workshop-search"; $APPINSIGHTS="schneider-workshop-ai"
```

```bash
az group create -n $RG -l $LOCATION
```

---

## 1. Microsoft Foundry resource + project

### Option A — Foundry portal (recommended for first-timers)

1. Go to **https://ai.azure.com** and sign in.
2. **Create a project** → choose **Create new resource** (this creates the
   underlying Foundry / Azure AI account) → name it (`schneider-foundry`),
   pick your subscription, resource group, and region.
3. Name the project `technician-copilot` and create it.
4. When it finishes, open the project and copy the **Project endpoint** from
   **Overview → Endpoints**. It looks like:
   ```
   https://<foundry>.services.ai.azure.com/api/projects/<project>
   ```
   → this becomes `AI_FOUNDRY_PROJECT_ENDPOINT` in your `.env`.

### Option B — Azure CLI

```bash
# The Foundry account (Cognitive Services, kind=AIServices)
az cognitiveservices account create \
  -n $FOUNDRY -g $RG -l $LOCATION \
  --kind AIServices --sku S0 \
  --custom-domain $FOUNDRY --yes

# Create the project (via the Foundry portal, or `az cognitiveservices account`
# project APIs / azd). The portal is the most reliable path today.
```

> The project endpoint host is `https://<foundry>.services.ai.azure.com`; the
> matching **Azure OpenAI** surface is
> `https://<foundry>.openai.azure.com/openai/v1` → `AZURE_OPENAI_ENDPOINT`.

---

## 2. Model deployments

Deploy **two** models into the Foundry resource. The deployment **names** must
match your `.env` (defaults shown).

| Purpose    | Model                     | Deployment name (default)          | `.env` variable                     |
|------------|---------------------------|------------------------------------|-------------------------------------|
| Chat       | `gpt-5.4` (or a `gpt-4o`/`gpt-4.1`-class model) | `gpt-5.4`             | `AZURE_AI_MODEL_DEPLOYMENT_NAME`    |
| Embeddings | `text-embedding-3-large`  | `text-embedding-3-large`           | `EMBEDDING_MODEL_DEPLOYMENT_NAME`   |
| Chat (small) *(Labs 07–08 only)* | `gpt-4.1-mini`  | `gpt-4.1-mini`           | `CU_GPT_MINI_DEPLOYMENT`   |

> The **`gpt-4.1-mini`** deployment is only needed for the advanced labs: Lab 07
> (Content Understanding) maps it, and Lab 08 (Guardrails) uses it as the cheap
> base model it wraps with a guardrails policy. Skip it if you stop at Lab 06.

### Portal
Project → **Models + endpoints** → **Deploy model** → pick the model → keep the
deployment name equal to the model id → set a generous **TPM** (tokens/min) quota
so ~20 participants don't throttle each other (e.g. 100K+ TPM on chat).

### CLI

```bash
az cognitiveservices account deployment create \
  -g $RG -n $FOUNDRY \
  --deployment-name gpt-5.4 \
  --model-name gpt-5.4 --model-format OpenAI --model-version "1" \
  --sku-capacity 100 --sku-name GlobalStandard

az cognitiveservices account deployment create \
  -g $RG -n $FOUNDRY \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large --model-format OpenAI --model-version "1" \
  --sku-capacity 100 --sku-name Standard
```

> If you deploy a **different chat model** (e.g. `gpt-4o`), set
> `AZURE_AI_MODEL_DEPLOYMENT_NAME` to that deployment name — the labs read it from
> `.env`, they don't hardcode `gpt-5.4`.

---

## 3. Azure AI Search (Labs 04, 05, 06)

Labs 04–06 build a vector + semantic index (`schneider-manuals-index`) of the
synthetic product manuals.

```bash
az search service create \
  -n $SEARCH -g $RG -l $LOCATION \
  --sku Basic --partition-count 1 --replica-count 1
```

- **Basic** tier is enough for this workshop (supports vector + semantic search).
- Copy the endpoint `https://<search>.search.windows.net` →
  `AZURE_AI_SEARCH_ENDPOINT`.

### Connect Search to the Foundry project

The labs read the Search connection from the **project's default AI Search
connection**. In the Foundry portal:

**Project → Management center → Connections → New connection → Azure AI Search**
→ select your Search service → **Authentication: API key** (simplest) *or*
**Microsoft Entra ID** → create.

> The labs auto-discover this connection via
> `connections.get_default(ConnectionType.AZURE_AI_SEARCH)` — you do **not** put
> the connection name in `.env`.

---

## 4. Application Insights (Lab 06 — observability)

Lab 06 sends OpenTelemetry traces to Application Insights.

```bash
# Log Analytics workspace (App Insights backing store)
az monitor log-analytics workspace create -g $RG -n schneider-law -l $LOCATION

WORKSPACE_ID=$(az monitor log-analytics workspace show \
  -g $RG -n schneider-law --query id -o tsv)

az monitor app-insights component create \
  -a $APPINSIGHTS -g $RG -l $LOCATION \
  --workspace $WORKSPACE_ID
```

**Attach it to the project** so `telemetry.get_application_insights_connection_string()`
works: Foundry portal → **Project → Tracing / Observability → connect an
Application Insights resource** → pick `$APPINSIGHTS`.

> If it's connected to the project, the lab discovers the connection string
> automatically. As a fallback you can set `APPLICATIONINSIGHTS_CONNECTION_STRING`
> in `.env` (copy it from the App Insights **Overview** blade).

---

## 5. RBAC — the roles that make keyless auth work

Assign these to **every participant** (or the group they belong to). Get a
principal's object id with `az ad user show --id <upn> --query id -o tsv`.

| Role | Scope | Why |
|------|-------|-----|
| **Azure AI User** | Foundry resource | Call the project, create agents, run models (Labs 00–06) |
| **Cognitive Services OpenAI User** | Foundry resource | Chat + embedding inference |
| **Search Index Data Contributor** | Search service | Build & upload to the index (Lab 04) |
| **Search Service Contributor** | Search service | Create the index definition (Lab 04) |
| **Monitoring Metrics Publisher** *(optional)* | App Insights | Publish traces (Lab 06) |
| **Cognitive Services User** *(Lab 07)* | Foundry resource | Call Content Understanding (keyless) |
| **Cognitive Services Contributor** *(Lab 08)* | Foundry resource | Create the RAI blocklist, policy & guardrailed deployment |

Example (grant to the signed-in user on the resource group; scope tighter in
production):

```bash
USER_OID=$(az ad signed-in-user show --query id -o tsv)
SUB=$(az account show --query id -o tsv)
RG_SCOPE="/subscriptions/$SUB/resourceGroups/$RG"

for ROLE in "Azure AI User" "Cognitive Services OpenAI User" \
            "Search Index Data Contributor" "Search Service Contributor"; do
  az role assignment create --assignee "$USER_OID" --role "$ROLE" --scope "$RG_SCOPE"
done
```

> Role assignments can take a few minutes to propagate. If Lab 04 fails with a
> `403` on the Search index, wait 5 minutes and retry before debugging code.

---

## 6. Verify

From a machine with `az login` done and `.env` filled in
(see [`setup.md`](./setup.md)), run **Lab 00 · setup-check** — it validates the
project connection, the chat model, and prints a green checklist. If Lab 00
passes, the environment is ready for the whole workshop.

---

## 7. Advanced labs (07–09) — extra prerequisites

The core labs stop at Lab 06. Labs **07–09** (Content Understanding, Guardrails,
Red Teaming) each need a little more provisioning. Do this only if you're running
the extended track.

### 7.1 Content Understanding (Lab 07)
- Content Understanding is a capability of your **existing Foundry / Azure AI
  Services** resource — **no separate resource** is needed. It is reached at the
  `https://<foundry>.services.ai.azure.com/` base URL (same host as the project),
  which Lab 07 derives from `AI_FOUNDRY_PROJECT_ENDPOINT`.
- Deploy the small **`gpt-4.1-mini`** chat model (see §2) — the prebuilt analyzers
  map it alongside `text-embedding-3-large`.
- Grant participants **Cognitive Services User** on the Foundry resource (keyless).

### 7.2 Guardrails (Lab 08)
- Lab 08 authors a Content Safety **RAI blocklist + policy** and creates a **new,
  dedicated guardrailed deployment** named `gpt-4.1-mini-guardrails` from the
  `gpt-4.1-mini` base (so the `gpt-5.4` production deployment is untouched).
- Ensure there is **spare model quota** for that extra deployment (it reuses the
  `gpt-4.1-mini` model, `GlobalStandard`, ~30 capacity).
- Grant participants **Cognitive Services Contributor** on the Foundry resource —
  this is the role that can create RAI policies. (Authoring RAI policies is a
  control-plane action, so `Azure AI User` alone is not enough.)
- Set **`AZURE_SUBSCRIPTION_ID`** in `.env` (or rely on `az account show`); the lab
  derives the account + resource group from the project endpoint automatically.
- **Pre-provision option:** if you don't want participants creating deployments,
  create the policy + `gpt-4.1-mini-guardrails` deployment **once** from the portal
  (Content filters → custom filter → attach the blocklist; Deployments → set the
  filter under *Advanced*) and have participants just read the deployment name.

### 7.3 Red Teaming (Lab 09)
- Lab 09 uses the **AI Red Teaming Agent** (`azure-ai-evaluation[redteam]`,
  PyRIT-backed) — already pinned in [`requirements.txt`](../requirements.txt).
- The project must be in a **region the Red Teaming Agent supports** — e.g.
  **East US 2**, **Sweden Central**, **France Central**, **Switzerland West**. If
  your Foundry project is elsewhere, the scan cannot run.
- The kernel must be **Python 3.10–3.13** (PyRIT excludes 3.9 and 3.14+).
- **Azure AI User** on the project (already granted for the core labs) is enough —
  the scan logs its results to the project. No extra role is required.

---

- **`403 Forbidden` / `AuthorizationFailure` / `ProjectMIUnauthorized`** — almost
  always **resource networking or RBAC**, not code. Check that the role
  assignments above have propagated, and that the Search service and any Storage
  account used for file search don't have a firewall `defaultAction = Deny` that
  blocks the Foundry service.
- **`Missing credentials` from `AzureOpenAI`** — a known bug with `openai==2.44.0`
  + AAD in this stack. The labs work around it by calling the embeddings REST
  endpoint with a bearer token (`config.embed_texts`). No action needed.
- **Model not found / deployment name mismatch** — confirm the deployment names
  in the Foundry portal exactly match `AZURE_AI_MODEL_DEPLOYMENT_NAME` and
  `EMBEDDING_MODEL_DEPLOYMENT_NAME` in `.env`.
