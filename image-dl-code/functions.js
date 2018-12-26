(function() {
  // These are my testable functions
  const getMediaURL = function(data) {
    if (data == null || data == "") {
      return "";
    }
    if (
      data.taxonConcept.dataObjects &&
      data.taxonConcept.dataObjects[0].mediaURL
    ) {
      const actual = data.taxonConcept.dataObjects[0].mediaURL;
      return actual;
    }
    return "";
  };

  const getKabobedName = function(data) {
    if (!data) {
      return "";
    }
    return replaceAll(replaceAll(data.toLowerCase(), " ", "-"), "'", "_");
  };

  const getUnKabobedName = function(data) {
    if (!data) {
      return "";
    }
    return capitalizeFirstLetter(
      replaceAll(replaceAll(data.toLowerCase(), "-", " "), "_", "'")
    );
  };

  const replaceAll = function(target, search, replacement) {
    return target.split(search).join(replacement);
  };

  const capitalizeFirstLetter = function(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  };

  class HttpPicker {
    constructor(http, https) {
      this.http = http;
      this.https = https;
    }
    gethttp(url) {
      if (url.startsWith("https")) {
        return this.https;
      }
      if (url.startsWith("http")) {
        return this.http;
      }
      return "";
    }
  }

  class LogObjects {
    constructor(level = "error") {
      this.objectList = [];
      switch (level) {
        case "error":
        case 2:
          this.level = 2;
          break;
        default:
          this.level = 1;
          break;
      }
    }
    log(newValue) {
      if (this.level <= 1) {
        this.objectList.push(newValue);
      }
    }
    error(newValue) {
      if (this.level <= 2) {
        this.objectList.push(newValue);
      }
    }
    toString() {
      if (this.objectList.length === 0) {
        return "";
      }
      // get the keys from the first object
      const obj1 = this.objectList[0];
      const titleRow = Object.keys(obj1).join(",");
      return (
        titleRow +
        "\n" +
        this.objectList
          .map(item => {
            return Object.values(item).join(",");
          })
          .join("\n")
      );
    }
  }

  module.exports = {
    getMediaURL,
    getKabobedName,
    getUnKabobedName,
    HttpPicker,
    LogObjects
  };
})();
