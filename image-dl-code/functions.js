// These are my testable functions
const getMediaURL = function(data) {
  if (data == null || data == "") {
    return "";
  }
  if (data.taxonConcept.dataObjects[0].mediaURL) {
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
  return capitalizeFirstLetter(replaceAll(replaceAll(data.toLowerCase(), "-", " "), "_", "'"));
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



module.exports = {
  getMediaURL,
  getKabobedName,
  getUnKabobedName,
  HttpPicker
};
