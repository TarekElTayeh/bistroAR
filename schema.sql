-- schema.sql
--
-- SQLite schema for the Bistro54 automation project.
-- Defines tables for clients, visits, visit_items, invoices,
-- invoice_items, and monthly_report. Additional tables
-- such as recon_issues may be added later.

PRAGMA foreign_keys = ON;

-- Clients table: stores basic client data imported from the
-- "client list" spreadsheet.
CREATE TABLE IF NOT EXISTS clients (
  code TEXT PRIMARY KEY,
  name TEXT,
  phone TEXT,
  address1 TEXT,
  address2 TEXT,
  prepaid_balance REAL,
  owed_amount REAL,
  email TEXT
);

-- Visits table: one row per visit (unique combination of
-- client_code, date, time and reference number). Summaries
-- of totals and taxes can be stored here.
CREATE TABLE IF NOT EXISTS visits (
  id TEXT PRIMARY KEY,
  client_code TEXT NOT NULL,
  date TEXT NOT NULL,
  time TEXT NOT NULL,
  reference TEXT NOT NULL,
  employee TEXT,
  subtotal REAL,
  tax_tps REAL,
  tax_tvq REAL,
  tip REAL,
  discount REAL,
  total REAL,
  FOREIGN KEY (client_code) REFERENCES clients(code)
);

-- Visit items table: one row per line item within a visit.
-- Contains the description and price charged.
CREATE TABLE IF NOT EXISTS visit_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  visit_id TEXT NOT NULL,
  description TEXT NOT NULL,
  price REAL NOT NULL,
  FOREIGN KEY (visit_id) REFERENCES visits(id)
);

-- Monthly report table: stores monthly balances from the
-- external monthly report for reconciliation. Period
-- should be of the form 'YYYY-MM'.
CREATE TABLE IF NOT EXISTS monthly_report (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_code TEXT NOT NULL,
  period TEXT NOT NULL,
  balance REAL NOT NULL,
  FOREIGN KEY (client_code) REFERENCES clients(code)
);

-- Invoices table: one row per generated invoice. Stores
-- aggregated totals for the invoice period.
CREATE TABLE IF NOT EXISTS invoices (
  id TEXT PRIMARY KEY,
  client_code TEXT NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  subtotal REAL,
  tax_tps REAL,
  tax_tvq REAL,
  total REAL,
  created_at TEXT,
  FOREIGN KEY (client_code) REFERENCES clients(code)
);

-- Invoice items table: one row per visit included on an
-- invoice. Links invoices to visits and stores the amount
-- attributed to that visit on the invoice.
CREATE TABLE IF NOT EXISTS invoice_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  invoice_id TEXT NOT NULL,
  visit_id TEXT NOT NULL,
  description TEXT,
  amount REAL NOT NULL,
  FOREIGN KEY (invoice_id) REFERENCES invoices(id),
  FOREIGN KEY (visit_id) REFERENCES visits(id)
);