const fs = require('fs')

module.exports.log = function(message) {
  module.exports.mkdir('tmp')
  fs.appendFileSync('tmp/log.txt', message + '\n')
}

module.exports.mkdir = function(dirname) {
  fs.existsSync(dirname) || fs.mkdirSync(dirname)
}

module.exports.readFile = function(filepath) {
  return fs.readFileSync(filepath, 'utf8')
}

module.exports.stdin = function() {
  return module.exports.readFile(0)
}
