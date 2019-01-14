  // These are files I got from data-parser/index.js
  const parse = require("csv-parse/lib/sync");
  const fs = require("fs");

  const parseCsv = function(filename) {
    const contents = fs.readFileSync(getPath(filename), "utf8");
    return parse(contents, {
      columns: true,
      skip_empty_lines: true
    });
  };

  const getPath = function(filename) {
    return "../data/" + filename;
  };

  module.exports = { parseCsv, getPath };
