const DownloadImages = require("./DownloadImages");
async function downloadImages() {
  const inputFileName = "species_native_status_EOL_ID_test.csv";
  //const inputFileName = "species_native_status_EOL_ID.csv";
  const outFileName = "../data/jpgs/csv/download_files_results.csv";
  const errorFilename = "../data/jpgs/csv/download_files_error.csv";
  const pngsPath = "../data/jpgs";
  const logLevel = "all";

  // create the object with settings
  const downloadImages = new DownloadImages({
    inputFileName,
    outFileName,
    errorFilename,
    pngsPath,
    logLevel
  });

  // run it
  await downloadImages.run();

  // this code shouldn't be called until downloadImages is done.
  console.log("done");
}
downloadImages();
