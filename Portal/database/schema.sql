-- Reference schema for production PostgreSQL deployments.
-- The FastAPI service also creates these tables through SQLAlchemy.

CREATE TABLE IF NOT EXISTS orders (
  id VARCHAR(128) PRIMARY KEY,
  account_id VARCHAR(128) NOT NULL,
  product_id VARCHAR(128) NOT NULL,
  amount_minor INTEGER NOT NULL,
  currency VARCHAR(16) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS payment_events (
  provider_event_id VARCHAR(256) PRIMARY KEY,
  provider VARCHAR(64) NOT NULL,
  order_id VARCHAR(128) NOT NULL,
  status VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS entitlements (
  id VARCHAR(128) PRIMARY KEY,
  account_id VARCHAR(128) NOT NULL,
  product_id VARCHAR(128) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS devices (
  id VARCHAR(256) PRIMARY KEY,
  account_id VARCHAR(128) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE
);
