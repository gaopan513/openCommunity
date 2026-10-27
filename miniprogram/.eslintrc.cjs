/* eslint-env node */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: ['eslint:recommended', 'plugin:vue/vue3-recommended'],
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  // uni-app 运行时全局变量（prettier 后 lint，warn 起步，存量清零后再升 error）
  globals: {
    uni: 'readonly',
    wx: 'readonly',
    getCurrentPages: 'readonly',
    App: 'readonly',
    Page: 'readonly',
    Component: 'readonly',
    __wxConfig: 'readonly',
  },
  rules: {
    // 与 .prettierrc 对齐，交由 prettier 负责格式
    'vue/max-attributes-per-line': 'off',
    'vue/html-self-closing': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    // 以下开启为 warn（容忍式起步），存量告警清零后可收紧
    // 保留错误/告警日志，禁止调试用 console.log
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-unused-vars': 'warn',
    'vue/no-unused-components': 'warn',
    'vue/multi-word-component-names': 'off',
  },
}