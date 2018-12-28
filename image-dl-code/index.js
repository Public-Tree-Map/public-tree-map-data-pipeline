const DownloadImages = require("./DownloadImages");

const inputFileName = "species_native_status_EOL_ID_test.csv";
//const inputFileName = "species_native_status_EOL_ID.csv";
const outFileName = "../data/jpgs/csv/download_files_results.csv";
const errorFilename = "../data/jpgs/csv/download_files_error.csv";
const pngsPath = "../data/jpgs";
(async function() {
  const logLevel = "all";

  const downloadImages = new DownloadImages({
    inputFileName,
    outFileName,
    errorFilename,
    pngsPath,
    logLevel
  });

  await downloadImages.run();
  console.log("done");
})();
