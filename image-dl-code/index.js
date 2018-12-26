const DownloadImages = require("./DownloadImages");

const { LogObjects } = require("./functions");

const inputFileName = "species_native_status_EOL_ID_test.csv";
//const inputFileName = "species_native_status_EOL_ID.csv";
const outFileName = "download_files_results.csv";
const pngsPath = "../data/jpgs";
(async function() {
  const logObjects = new LogObjects("all");

  const downloadImages = new DownloadImages(
    inputFileName,
    outFileName,
    pngsPath,
    logObjects
  );

  await downloadImages.run();
  console.log("done");
})();
