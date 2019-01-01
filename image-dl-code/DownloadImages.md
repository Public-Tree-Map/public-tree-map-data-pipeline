# DownloadImages

## Assumptions

The file **inputFileName** is a CSV file that contains the columns **EOL\_ID** and **botanical\_name**.

I hard coded the URL of eol.org's API. Look in the method makeFetchUrl() if you need to change it.

## Run the code

```javascript
// Include DownloadImages
const DownloadImages = require("./DownloadImages");

// create the object with settings
const downloadImages = new DownloadImages(settings);

// run it
await downloadImages.run();
```

## Settings

Settings are passed to DownloadImages's constructor as an object with the following fields

| Setting | Purpose | Example |
|---------|---------|---------|
| inputFileName | A CSV file that will be read the lines will be processed | |
| outFileName   | Sucesses will be written to this file | |
| errorFilename | Errors will be written to this file | |
| pngsPath      | This is where the images will be wrriten | |
| logLevel      | | |

## Process

### The Happy Path

- Read the content of **inputFileName** as a CSV file

- Remember the value from the **EOL\_ID** and **botanical\_name** column

- Use the **EOL\_ID** value to make an API call to [eol.org](https://eol.org)

- If the respose status is 200:

- Parse the **mediaURL** from the JSON

- Fetch the image from the we using **mediaURL**. Sometimes we get 300 errors, see "Fetch Image Retry" for more information

- Convert **botanical\_name** to **image\_file\_name** by replacing spaces with minus signs and adding the extension (png, jpg, etc.)

- Save image to **pngsPath** using the **image\_file\_name**

- Log success to **outFileName**

### Fetch Image Retry

Some times I got 301 or 302 when fetching images. I only go 1 level of redirection. Here is the process:

- Get **location** from response headers

- Use **location** to fetch the image files (just like above)

- Convert **botanical\_name** to **image\_file\_name** by replacing spaces with minus signs and adding the extension (png, jpg, etc.)

- Save image to **pngsPath** using the **image\_file\_name**

- Log success after redirect to **outFileName**

### Errors

## Logging

| Field | Descrition |
|-----|----------|
| *item* | The line from **inputFileName**, there will be more than 1 column in this position |
| responseCode | The HTTP response code this time |
| firstCode | The HTTP response code from the previous time (should only be 302 or 302) |
| mediaURL | The URL of the image that the script downloads |
| writtenFile  | The name of the file that the script writes |
| error | The text of any error message written (blank if no error ) |