const policyBridge = require('./policyBridge');
const expoVideoAdapter = require('./expoVideoAdapter');
const reactNativeVideoAdapter = require('./reactNativeVideoAdapter');

module.exports = {
  ...policyBridge,
  ...expoVideoAdapter,
  ...reactNativeVideoAdapter,
};\n