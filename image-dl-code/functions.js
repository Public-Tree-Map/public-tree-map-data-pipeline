<<<<<<< HEAD
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
/**
 * LogObjects
 */
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
    log(value) {
      //if (this.level <= 1) {
      this.objectList.push({ value, key: "log" });
      //}
    }
    error(value) {
      //if (this.level <= 2) {
      this.objectList.push({ value, key: "error" });
      //}
    }
    getError() {
      return this.getCsv(function(item) {
        return item.key === "error";
      });
    }
    getLogged() {
      return this.getCsv(function(item) {
        return item.key === "log";
      });
    }
    getAll() {
      return this.getCsv(function() {
        return true;
      });
    }
    getCsv(filterFunction) {
      const errors = this.objectList.filter(filterFunction);
      if (errors.length === 0) {
        return "";
      }
      // get the keys from the first object
      const obj1 = errors[0];
      const titleRow = Object.keys(obj1.value).join(",");
      return (titleRow +
        "\n" +
        errors
          .map(item => {
            return Object.values(item.value).join(",");
          })
          .join("\n"));
    }
    // toString() {
    //   let filterFunction;
    //   switch (this.level) {
    //     case "error":
    //     case 2:
    //       filterFunction = item => item.key === "error";
    //       break;
    //     default:
    //       filterFunction = () => true;
    //       break;
    //   }
    //   return this.getCsv(filterFunction);
    // }
  }

  module.exports = {
    getMediaURL,
    getKabobedName,
    getUnKabobedName,
    HttpPicker,
    LogObjects
  };
})();
=======
// These are my testable functions
const getMediaURL = function(data) {
  if (data == null || data == "") {
    return "";
  }
  if (data.taxonConcept.dataObjects && data.taxonConcept.dataObjects[0].mediaURL) {
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
  constructor() {
    this.objectList = [];
  }
  log(newValue) {
    if (this.objectList.length === 0) {
      console.log(Object.keys(newValue).join(","));  
    }
    console.log(Object.values(newValue).join(","));
    this.objectList.push(newValue);
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
>>>>>>> Public-Tree-Map/master
