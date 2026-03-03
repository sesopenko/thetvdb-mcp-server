module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Full header (type(scope): subject) must not exceed 50 chars
    'header-max-length': [2, 'always', 50],
    // Scope is required on every commit
    'scope-empty': [2, 'never'],
    // Body is required on every commit
    'body-empty': [2, 'never'],
    // No trailing period on subject
    'subject-full-stop': [2, 'never', '.'],
  },
};
