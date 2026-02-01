import { check } from 'k6';
import { Rate } from 'k6/metrics';
import sql from 'k6/x/sql';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up
    { duration: '1m', target: 10 },  // Stay at 10 users
    { duration: '30s', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must be below 500ms
    errors: ['rate<0.1'],            // Error rate should be less than 10%
  },
};

// Database connection - adjust these values based on your .env
const DB_URL = __ENV.DB_URL || 'postgres://postgres:password@localhost:6432/postgres?sslmode=disable';

export default function () {
  // Open database connection
  const db = sql.open('postgres', DB_URL);
  
  try {
    // Test basic SELECT query
    let result = sql.query(db, 'SELECT NOW() as current_time, version() as pg_version');
    
    check(result, {
      'query executed successfully': (r) => r.length > 0,
      'timestamp returned': (r) => r[0].current_time !== null,
    });

    // Test INSERT into audit_test table
    const testName = `load-test-${Math.random().toString(36).substr(2, 9)}`;
    let insertResult = sql.query(db, 'INSERT INTO audit_test (name) VALUES ($1) RETURNING id', testName);
    
    check(insertResult, {
      'insert executed successfully': (r) => r.length > 0,
      'got inserted id': (r) => r[0].id > 0,
    });

    // Test SELECT from audit_test table  
    let selectResult = sql.query(db, 'SELECT COUNT(*) as count FROM audit_test');
    
    check(selectResult, {
      'count query executed': (r) => r.length > 0,
      'table has records': (r) => r[0].count > 0,
    });

  } catch (error) {
    console.error(`Database query failed: ${error}`);
    errorRate.add(1);
  } finally {
    // Close database connection
    db.close();
  }
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    '/tmp/k6-results.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  // Simple text summary
  return `
Test Results Summary:
- Total requests: ${data.metrics.http_reqs ? data.metrics.http_reqs.values.count : 'N/A'}
- Average duration: ${data.metrics.http_req_duration ? data.metrics.http_req_duration.values.avg.toFixed(2) + 'ms' : 'N/A'}
- Error rate: ${data.metrics.errors ? (data.metrics.errors.values.rate * 100).toFixed(2) + '%' : 'N/A'}
`;
}
