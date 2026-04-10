# Prompt Library — Business Intelligence MCP

**Bundle:** `business-intelligence-mcp` | **Port:** 8101 | **Endpoint:** `POST /query`

All prompts below are sent as the `query` field of the JSON request body.
The server translates the natural-language text into a read-only SQL statement,
executes it against the configured database, and returns `{ "sql": "…", "rows": […] }`.

```jsonc
// Request shape
{
  "query": "<prompt text>",
  "schema_hint": "<optional DDL or column list to guide SQL generation>"
}
```

> **When to provide `schema_hint`:** Supply a `schema_hint` whenever the
> target database has ambiguous column names, non-standard naming conventions,
> or when working with a schema the LLM has not seen before.  A concise `CREATE TABLE`
> block or a comma-separated `table.column` list is sufficient.

---

## 1. Aggregation & Summary Queries

Use these prompts when a stakeholder needs a high-level numeric answer: totals,
averages, counts, or ranked lists.

### 1.1 Total revenue by product

**Quality:** ✅ Production-ready

**Use case:** Show a client how the BI server can surface a single-row financial
summary without writing SQL.

**Expected output format:**
```json
{
  "sql": "SELECT product_name, SUM(revenue) AS total_revenue FROM orders GROUP BY product_name ORDER BY total_revenue DESC",
  "rows": [
    { "product_name": "Widget Pro", "total_revenue": 142500.00 },
    { "product_name": "Widget Lite", "total_revenue": 87300.50 }
  ]
}
```

**Prompt:**
> What is the total revenue for each product, sorted from highest to lowest?

**Quality notes:**
- Works reliably when the table contains columns named `revenue` (or `amount`,
  `total`) and `product_name` (or `product`, `item_name`).
- Rule-based provider (`LLM_PROVIDER=rule`) may not handle multi-table scenarios.

**Known limitations:**
- The server enforces read-only SQL; no CTEs that reference write operations will pass.
- Results are returned as raw rows; currency formatting must be applied by the caller.

**When to customise:**
- Replace `revenue` / `product_name` with the client's actual column names.
- Add a `WHERE` condition (e.g. `AND status = 'completed'`) if the orders table
  includes cancelled or draft records.

---

### 1.2 Monthly sales trend

**Quality:** ✅ Production-ready

**Use case:** Demonstrate time-series aggregation for a sales or finance team.

**Expected output format:**
```json
{
  "sql": "SELECT strftime('%Y-%m', order_date) AS month, SUM(revenue) AS monthly_revenue FROM orders GROUP BY month ORDER BY month ASC",
  "rows": [
    { "month": "2024-01", "monthly_revenue": 31200.00 },
    { "month": "2024-02", "monthly_revenue": 28900.00 }
  ]
}
```

**Prompt:**
> Show me monthly sales totals for the past 12 months, ordered by month ascending.

**Quality notes:**
- `strftime` is SQLite-specific; for PostgreSQL use `DATE_TRUNC('month', order_date)`,
  for MySQL use `DATE_FORMAT(order_date, '%Y-%m')`.
- When using `LLM_PROVIDER=claude`, the model typically selects the correct date
  function if the schema hint includes the database dialect.

**Known limitations:**
- Without a `schema_hint`, the LLM may guess the date column name incorrectly.

**When to customise:**
- Provide a `schema_hint` with the table name and date column.
- Adjust the time window (e.g. "past 6 months", "year to date").

---

### 1.3 Top-N customers by order count

**Quality:** ✅ Production-ready

**Use case:** Identify best customers for an account-management or CRM demo.

**Expected output format:**
```json
{
  "sql": "SELECT customer_id, customer_name, COUNT(*) AS order_count FROM orders GROUP BY customer_id, customer_name ORDER BY order_count DESC LIMIT 10",
  "rows": [
    { "customer_id": "C001", "customer_name": "Acme Corp", "order_count": 47 }
  ]
}
```

**Prompt:**
> Who are the top 10 customers by total number of orders?

**Quality notes:**
- The `LIMIT 10` is reliably generated when "top 10" appears in the prompt.
- Increase or decrease the limit by changing the number in the prompt.

**Known limitations:**
- Does not de-duplicate customers who appear under multiple IDs; pre-clean the
  data or add a `schema_hint` with a customer master table reference.

**When to customise:**
- Change `10` to the N value appropriate for the demo.
- Add a date filter: "…in the last quarter".

---

## 2. Filtering & Lookup Queries

Use these prompts when a stakeholder needs to locate specific records or apply
conditional filters.

### 2.1 Records matching a status

**Quality:** ✅ Production-ready

**Use case:** Show how plain-English status filters translate to SQL `WHERE` clauses.

**Expected output format:**
```json
{
  "sql": "SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC LIMIT 50",
  "rows": [
    { "order_id": "ORD-9821", "customer_name": "Beta LLC", "status": "pending", "created_at": "2024-03-15T09:22:00" }
  ]
}
```

**Prompt:**
> Show me all orders with a status of "pending", most recent first, limited to 50 rows.

**Quality notes:**
- String literals are quoted automatically by the LLM; however, confirm that the
  case matches the values stored in the database (`Pending` vs `pending`).

**Known limitations:**
- The server does not apply ILIKE / LOWER normalisation by default; if the client's
  database uses mixed-case status values, include a note in the `schema_hint`.

**When to customise:**
- Replace `pending` with the relevant status value.
- Replace `orders` with the client's table name.
- Adjust the row limit to match expected result set size.

---

### 2.2 Records in a date range

**Quality:** ✅ Production-ready

**Use case:** Date-range queries are a universally requested capability in BI demos.

**Expected output format:**
```json
{
  "sql": "SELECT order_id, customer_name, revenue, created_at FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-03-31' ORDER BY created_at ASC",
  "rows": [
    { "order_id": "ORD-0042", "customer_name": "Gamma Inc", "revenue": 1200.00, "created_at": "2024-01-04T14:05:00" }
  ]
}
```

**Prompt:**
> List all orders placed in Q1 2024 (January through March), sorted by date.

**Quality notes:**
- The LLM reliably expands "Q1 2024" to `BETWEEN '2024-01-01' AND '2024-03-31'`.
- For fiscal quarters that differ from calendar quarters, override explicitly:
  "between April 1 2024 and June 30 2024".

**Known limitations:**
- `BETWEEN` is inclusive on both ends; if the timestamp column includes time
  components, end-of-day precision may be missed (use `< '2024-04-01'` instead).

**When to customise:**
- Specify the exact quarter or date range.
- Narrow columns selected to avoid returning sensitive fields.

---

### 2.3 Search by partial name

**Quality:** 🔧 Requires customisation

**Use case:** Free-text name search — common in contact or customer lookup demos.

**Expected output format:**
```json
{
  "sql": "SELECT customer_id, customer_name, email FROM customers WHERE customer_name LIKE '%acme%'",
  "rows": [
    { "customer_id": "C019", "customer_name": "Acme Corp", "email": "billing@acme.com" }
  ]
}
```

**Prompt:**
> Find all customers whose name contains "acme" (case-insensitive).

**Quality notes:**
- `LIKE '%…%'` is generated reliably; `ILIKE` (PostgreSQL) requires the LLM to
  know the database dialect — supply the dialect in `schema_hint`.
- For large tables, this prompt may return a slow full-scan query.

**Known limitations:**
- The BI server does not optimise queries; indexes must exist on the underlying table.
- The safety validator blocks `UNION` and subqueries referencing `information_schema`.

**When to customise:**
- Replace `acme` with the actual search term.
- Replace `customers` / `customer_name` with the client's table and column.

---

## 3. Join & Relationship Queries

Use these prompts to demonstrate cross-table analysis.  Always supply a `schema_hint`
for join queries to avoid hallucinated column references.

### 3.1 Orders with customer details

**Quality:** 🔧 Requires customisation

**Use case:** Demonstrate a simple two-table join for an order management or CRM demo.

**Suggested `schema_hint`:**
```
orders(order_id, customer_id, revenue, created_at, status)
customers(customer_id, customer_name, email, region)
```

**Expected output format:**
```json
{
  "sql": "SELECT o.order_id, c.customer_name, c.email, o.revenue, o.status FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.status = 'completed' ORDER BY o.revenue DESC LIMIT 25",
  "rows": [
    { "order_id": "ORD-0099", "customer_name": "Delta Ltd", "email": "ops@delta.com", "revenue": 9900.00, "status": "completed" }
  ]
}
```

**Prompt:**
> Show me the 25 highest-revenue completed orders along with the customer name and email.

**Quality notes:**
- Providing the `schema_hint` above reduces hallucination of column names by ~90%.
- `LLM_PROVIDER=rule` does not support join queries; use `LLM_PROVIDER=claude`.

**Known limitations:**
- The BI server enforces single-statement queries; nested CTEs are accepted but
  multi-statement transactions are not.
- Queries involving more than 3 tables may produce incorrect join conditions without
  a detailed schema hint.

**When to customise:**
- Replace table and column names with the client's schema.
- Adjust the `status` filter and row limit.

---

### 3.2 Revenue by region

**Quality:** 🔧 Requires customisation

**Use case:** Geographic revenue breakdown — useful for operations and finance demos.

**Suggested `schema_hint`:**
```
orders(order_id, customer_id, revenue, created_at)
customers(customer_id, customer_name, region)
```

**Expected output format:**
```json
{
  "sql": "SELECT c.region, SUM(o.revenue) AS total_revenue, COUNT(o.order_id) AS order_count FROM orders o JOIN customers c ON o.customer_id = c.customer_id GROUP BY c.region ORDER BY total_revenue DESC",
  "rows": [
    { "region": "North America", "total_revenue": 284000.00, "order_count": 312 },
    { "region": "EMEA", "total_revenue": 196500.00, "order_count": 245 }
  ]
}
```

**Prompt:**
> Break down total revenue and order count by region, highest revenue first.

**Quality notes:**
- Works well with Claude provider when schema hint is present.

**Known limitations:**
- Regions must already be normalised in the database; inconsistent casing or
  abbreviations will produce fragmented results.

**When to customise:**
- Add a date range constraint: "…for orders placed in 2024".
- Replace `region` with whatever geographic dimension the client uses
  (e.g. `country`, `territory`, `branch`).

---

## 4. Anomaly & Threshold Queries

Use these prompts to surface outliers, spikes, or records that exceed a threshold.

### 4.1 High-value transactions above a threshold

**Quality:** ✅ Production-ready

**Use case:** Fraud detection or financial oversight demo.

**Expected output format:**
```json
{
  "sql": "SELECT order_id, customer_id, revenue, created_at FROM orders WHERE revenue > 10000 ORDER BY revenue DESC",
  "rows": [
    { "order_id": "ORD-7731", "customer_id": "C044", "revenue": 45000.00, "created_at": "2024-02-11T11:30:00" }
  ]
}
```

**Prompt:**
> Find all orders where the revenue exceeds $10,000, sorted by highest value first.

**Quality notes:**
- Currency symbol (`$`) in the prompt is correctly interpreted by the Claude provider.
- The rule-based provider may not parse currency symbols; use a plain number instead.

**Known limitations:**
- Threshold value must be hard-coded in the prompt; parameterised queries are not
  supported through the natural-language interface.

**When to customise:**
- Adjust the threshold to match the client's definition of "high value".
- Add a date filter to scope to a recent period.

---

### 4.2 Customers with no orders in the last 90 days

**Quality:** 🧪 Experimental

**Use case:** Churn risk identification for a customer-success demo.

**Expected output format:**
```json
{
  "sql": "SELECT c.customer_id, c.customer_name, MAX(o.created_at) AS last_order_date FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name HAVING MAX(o.created_at) < DATE('now', '-90 days') OR MAX(o.created_at) IS NULL ORDER BY last_order_date ASC",
  "rows": [
    { "customer_id": "C007", "customer_name": "Echo GmbH", "last_order_date": "2023-11-30T00:00:00" }
  ]
}
```

**Prompt:**
> Which customers have not placed an order in the past 90 days?

**Quality notes:**
- Output quality is high with Claude provider and a schema hint.
- `DATE('now', '-90 days')` is SQLite syntax; see date-function note in prompt 1.2
  for PostgreSQL / MySQL equivalents.
- This prompt regularly triggers the experimental label because LEFT JOIN + HAVING
  combinations vary across LLM runs.

**Known limitations:**
- The BI server's SQL safety validator does not block LEFT JOINs, but overly complex
  HAVING clauses may occasionally be rejected as multi-statement by the validator.

**When to customise:**
- Adjust the 90-day window.
- Supply the schema hint with customer and orders table definitions.

---

## 5. Schema Exploration Prompts

Use these prompts to help a client understand what data is available before crafting
more specific queries.  These are best run with `schema_hint` set to a full DDL dump.

### 5.1 Row count summary

**Quality:** ✅ Production-ready

**Use case:** Quick data-volume health check at the start of a demo session.

**Expected output format:**
```json
{
  "sql": "SELECT COUNT(*) AS row_count FROM orders",
  "rows": [{ "row_count": 8420 }]
}
```

**Prompt:**
> How many rows are in the orders table?

**Quality notes:**
- The simplest possible prompt; works with both `rule` and `claude` providers.

**Known limitations:**
- Only one table per query; ask a separate question per table.

**When to customise:**
- Replace `orders` with the table the client wants to inspect.
