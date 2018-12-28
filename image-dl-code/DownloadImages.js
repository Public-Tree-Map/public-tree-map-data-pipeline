(function() {
  const https = require("https");
  const http = require("http");
  const fetch = require("node-fetch");
  const path = require("path");
  const fs = require("fs");

  const {
    HttpPicker,
    getMediaURL,
    getKabobedName,
    LogObjects
  } = require("./functions");
  const { parseCsv } = require("./shared");

  const DownloadImages = function({
    inputFileName,
    outFileName,
    errorFilename,
    pngsPath,
    logLevel
  }) {
    this.inputFileName = inputFileName;
    this.outFileName = outFileName;
    this.errorFilename = errorFilename;
    this.pngsPath = pngsPath;
    this.logObjects = new LogObjects(logLevel);
  };

  DownloadImages.prototype.run = async function() {
    const httpPicker = new HttpPicker(http, https);

    try {
      await ensureDirectories(this.pngsPath);

      // load contents of file into an array of objects
      const list = parseCsv(this.inputFileName);
      for (const item of list) {
        let status, mediaURL;
        if (item.EOL_ID) {
          try {
            const fetchUrl = this.makeFetchUrl(item.EOL_ID);
            const response = await fetch(fetchUrl);
            const { status } = response;
            if (status == 200) {
              const json = await response.json();
              mediaURL = await getMediaURL(json);
              if (mediaURL) {
                await writeImageFile(
                  mediaURL,
                  item,
                  httpPicker,
                  this.logObjects,
                  this.pngsPath
                );
              } else {
                throw new Error(
                  `No mediaURL for EOL_ID ${item.EOL_ID}; URL: ${fetchUrl}`
                );
              }
            } else {
              throw new Error(
                `status: ${status}; EOL_ID: ${item.EOL_ID}; URL: ${fetchUrl}`
              );
            }
          } catch (err) {
            await this.logObjects.error({
              ...item,
              responseCode: status,
              firstCode: "",
              mediaURL,
              writtenFile: "",
              error: err.message
            });
          }
        } else {
          await this.logObjects.error({
            ...item,
            responseCode: status,
            firstCode: "",
            mediaURL,
            writtenFile: "",
            error: "No EOL ID"
          });
        }
      }
      writeTextFile(this.outFileName, this.logObjects.getLogged());
      writeTextFile(this.errorFilename, this.logObjects.getError());
    } catch (err) {
      console.log(err.message);
    }
  };
  DownloadImages.prototype.makeFetchUrl = function(EolId) {
    return `http://eol.org/api/pages/1.0.json?id=${EolId}&details=true&taxonomy=false&images_per_page=1`;
  };

  const writeTextFile = function(filename, contents) {
    if (filename) {
      fs.writeFileSync(filename, contents);
      console.log(`Wrote ${filename}`);
    }
    return true;
  };

  const writeImageFile = async function(
    mediaURL,
    item,
    httpPicker,
    logObjects,
    pngsPath
  ) {
    // Do we want to use EOL_ID or botanical_name to name the jpg files?
    const myHttp = await httpPicker.gethttp(mediaURL);
    return await myHttp
      //.gethttp(mediaURL)
      .get(mediaURL, async function(response) {
        switch (response.statusCode) {
          case 200: {
            return await writeStreamToFile(
              response,
              mediaURL,
              item,
              "",
              pngsPath,
              logObjects
            );
          }
          case 301:
          case 302: {
            // The HTTP response status code 302 Found is a common way of performing URL redirection.
            // Make 1 attempt at getting redirected resource
            // The redirected resource is in headers.location
            const {
              headers: { location }
            } = response;
            return httpPicker
              .gethttp(location)
              .get(location, async function(response2) {
                if (response2.statusCode == 200) {
                  return await writeStreamToFile(
                    response2,
                    mediaURL,
                    item,
                    response.statusCode,
                    pngsPath,
                    logObjects
                  );
                }
                return await writeOtherToFile(
                  response2,
                  item,
                  response.statusCode,
                  pngsPath,
                  logObjects,
                  "Redirect Failed"
                );
              });
          }
          default: {
            // All other codes
            return await writeOtherToFile(
              response,
              item,
              response.statusCode,
              pngsPath,
              logObjects,
              "Unexpected Status"
            );
          }
        }
      });
  };

  const writeStreamToFile = async function(
    response,
    mediaURL,
    item,
    firstCode,
    pngsPath,
    logObjects
  ) {
    const ext = path.extname(mediaURL);
    const ourFileName = `${pngsPath}/${getKabobedName(
      item.botanical_name
    )}${ext}`;
    await logObjects.log({
      ...item,
      responseCode: 200,
      firstCode,
      mediaURL,
      writtenFile: ourFileName,
      error: ""
    });
    var file = await fs.createWriteStream(ourFileName);
    return await response.pipe(file);
  };

  const writeOtherToFile = async function(
    response,
    item,
    firstCode,
    pngsPath,
    logObjects,
    error = ""
  ) {
    const ourFileName = `${pngsPath}/other/${getKabobedName(
      item.botanical_name
    )}_${response.statusCode}.html`;
    await logObjects.error({
      ...item,
      responseCode: response.statusCode,
      firstCode,
      mediaURL: response.headers.location,
      writtenFile: ourFileName,
      error
    });
    var file = await fs.createWriteStream(ourFileName);
    return await response.pipe(file);
  };

  const ensureDirectories = async function(basePath) {
    if (!fs.existsSync(basePath)) {
      await fs.mkdirSync(basePath);
    }
    if (!fs.existsSync(`${basePath}/other`)) {
      await fs.mkdirSync(`${basePath}/other`);
    }
    if (!fs.existsSync(`${basePath}/csv`)) {
      await fs.mkdirSync(`${basePath}/csv`);
    }
  };

  module.exports = DownloadImages;
})();
