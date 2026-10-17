import { describe, it, expect, beforeEach } from 'vitest';
import { api } from '../src/services/api';

describe('ApiClient', () => {
  beforeEach(() => {
    api.setToken(null);
  });

  it('manages JWT token in memory and getter/setter correctly', () => {
    expect(api.getToken()).toBeNull();
    api.setToken('test-jwt-token-123');
    expect(api.getToken()).toBe('test-jwt-token-123');

    api.setToken(null);
    expect(api.getToken()).toBeNull();
  });
});
