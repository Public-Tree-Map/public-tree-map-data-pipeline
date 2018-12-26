// some basic Unit Tests:
// $ npm run test
const chai = require("chai");
const expect = chai.expect;
const should = chai.should;

const {
  getMediaURL,
  getKabobedName,
  getUnKabobedName,
  HttpPicker,
  LogObjects
} = require("./functions");

describe("getMediaURL", function() {
  it("Should parse mediaURL from json", function() {
    const EXPECTED_FILE =
      "https://farm5.staticflickr.com/4013/4447875232_5d800ebd31_o.jpg";
    const TESTDATA = `{"taxonConcept":{"identifier":583608,"scientificName":"Arbutus unedo L.","richness_score":null,"dataObjects":[{"identifier":"EOL-media-542-4447875232","dataObjectVersionID":6686588,"dataType":"http://purl.org/dc/dcmitype/StillImage","dataSubtype":"jpg","vettedStatus":"Trusted","dataRatings":[],"dataRating":"2.5","mimeType":"image/jpeg","created":"2018-05-23T13:19:48.000Z","modified":"2018-10-20T02:38:34.000Z","title":"Arbutus unedo L. /    Madroo","license":"http://creativecommons.org/licenses/by-nc-sa/2.0/","license_id":4,"rightsHolder":"Jos Mara Escolano","source":"https://www.flickr.com/photos/valdelobos/4447875232/","mediaURL":"${EXPECTED_FILE}","description":"Pantano de la Pea: Huesca.Familia: ERICACEAEDistribucin:  NW de Irlanda, N de frica, Macaronesia, Palestina y S de Europa. Se encuentra por casi toda la Pennsula Ibrica, y en Aragn por las zonas templadas, llegando hasta el Prepirineo.Hbitat: Lugares abrigados en barrancos, carrascales, pinares de pino carrasco, y rara vez, en sotos fluviales.Preferencia edfica:  Acidfila. Prefiere los suelos descalcificados sobre conglomerados o areniscas.Rango altitudinal: ( 265 ) 350- 900 ( 1140 ) mFenologa: Floracin ( Octubre ) Noviembre - Enero ( Febrero )Fructificacin: Noviembre - EneroForma Biolgica: Macrofanerfito perennifolioExtractado del Atlas de la Flora de Aragn     (Herbario de Jaca)","eolMediaURL":"https://content.eol.org/data/media/7f/f3/db/542.4447875232.jpg","eolThumbnailURL":"https://content.eol.org/data/media/7f/f3/db/542.4447875232.98x68.jpg","agents":[{"full_name":"<a href='http://www.flickr.com/photos/42786943@N07'>Jos Mara Escolano</a>","homepage":"http://www.flickr.com/photos/42786943@N07","role":"photographer"},{"full_name":"Flickr Group","homepage":null,"role":"provider"}]}],"licenses":[]}}`;
    const data = JSON.parse(TESTDATA);

    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });
  it("mediaURL not in object, should parse as ''", function() {
    const EXPECTED_FILE = "";
    const TESTDATA = `{"taxonConcept":{"identifier":583608,"scientificName":"Arbutus unedo L.","richness_score":null,"dataObjects":[{"identifier":"EOL-media-542-4447875232","dataObjectVersionID":6686588,"dataType":"http://purl.org/dc/dcmitype/StillImage","dataSubtype":"jpg","vettedStatus":"Trusted","dataRatings":[],"dataRating":"2.5","mimeType":"image/jpeg","created":"2018-05-23T13:19:48.000Z","modified":"2018-10-20T02:38:34.000Z","title":"Arbutus unedo L. /    Madroo","license":"http://creativecommons.org/licenses/by-nc-sa/2.0/","license_id":4,"rightsHolder":"Jos Mara Escolano","source":"https://www.flickr.com/photos/valdelobos/4447875232/","description":"Pantano de la Pea: Huesca.Familia: ERICACEAEDistribucin:  NW de Irlanda, N de frica, Macaronesia, Palestina y S de Europa. Se encuentra por casi toda la Pennsula Ibrica, y en Aragn por las zonas templadas, llegando hasta el Prepirineo.Hbitat: Lugares abrigados en barrancos, carrascales, pinares de pino carrasco, y rara vez, en sotos fluviales.Preferencia edfica:  Acidfila. Prefiere los suelos descalcificados sobre conglomerados o areniscas.Rango altitudinal: ( 265 ) 350- 900 ( 1140 ) mFenologa: Floracin ( Octubre ) Noviembre - Enero ( Febrero )Fructificacin: Noviembre - EneroForma Biolgica: Macrofanerfito perennifolioExtractado del Atlas de la Flora de Aragn     (Herbario de Jaca)","eolMediaURL":"https://content.eol.org/data/media/7f/f3/db/542.4447875232.jpg","eolThumbnailURL":"https://content.eol.org/data/media/7f/f3/db/542.4447875232.98x68.jpg","agents":[{"full_name":"<a href='http://www.flickr.com/photos/42786943@N07'>Jos Mara Escolano</a>","homepage":"http://www.flickr.com/photos/42786943@N07","role":"photographer"},{"full_name":"Flickr Group","homepage":null,"role":"provider"}]}],"licenses":[]}}`;
    const data = JSON.parse(TESTDATA);

    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });
  it("null should parse as ''", function() {
    const EXPECTED_FILE = "";
    const data = null;

    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });
  it("'' should parse as ''", function() {
    const EXPECTED_FILE = "";
    const data = "";

    //const actual = data.taxonConcept.dataObjects[0].mediaURL;
    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });
  it("Should parse mediaURL from json different pattern", function() {
    const EXPECTED_FILE =
      "http://www.boldsystems.org/pics/SAFH/OM2818.Olea.europa.africana.1+1284733982.JPG";
    const TESTDATA = `{"taxonConcept":{"identifier":579181,"scientificName":"Olea europaea L.","richness_score":null,"dataObjects":[{"identifier":"EOL-media-539-SAFH/OM2818.Olea.europa.africana.1+1284733982.JPG","dataObjectVersionID":6013373,"dataType":"http://purl.org/dc/dcmitype/StillImage","dataSubtype":"jpg","vettedStatus":"Trusted","dataRatings":[],"dataRating":"2.5","mimeType":"image/jpeg","created":"2018-05-14T22:03:08.000Z","modified":"2018-10-20T01:11:28.000Z","license":"http://creativecommons.org/licenses/by-nc-sa/3.0/","license_id":5,"rightsHolder":"University of Johannesburg. Olivier Maurin. Year: 2011.","source":"http://www.boldsystems.org/index.php/Taxbrowser_Taxonpage?taxid=191897","mediaURL":"http://www.boldsystems.org/pics/SAFH/OM2818.Olea.europa.africana.1+1284733982.JPG","description":"Specimen..","eolMediaURL":"https://content.eol.org/data/media/7a/61/d8/539.SAFH_OM2818_Olea_europa_africana_1_1284733982_JPG.jpg","eolThumbnailURL":"https://content.eol.org/data/media/7a/61/d8/539.SAFH_OM2818_Olea_europa_africana_1_1284733982_JPG.98x68.jpg","agents":[{"full_name":"Olivier Maurin","homepage":null,"role":"photographer"},{"full_name":"Barcode of Life Data Systems","homepage":null,"role":"provider"}]}],"licenses":[]}}`;
    const data = JSON.parse(TESTDATA);

    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });

  it("Valid JSON, no URL to be found", function() {
    const EXPECTED_FILE =
      "";
    const TESTDATA = '{"taxonConcept":{"identifier":486203,"scientificName":"Pittosporum napaulense (DC.) Rehder \u0026 E.H. Wilson","richness_score":null,"licenses":[]}}';
    const data = JSON.parse(TESTDATA);

    const actual = getMediaURL(data);

    expect(actual).to.equal(EXPECTED_FILE);
  });
  //{"taxonConcept":{"identifier":486203,"scientificName":"Pittosporum napaulense (DC.) Rehder \u0026 E.H. Wilson","richness_score":null,"licenses":[]}}
});

describe("getKabobedName", function() {
  it("Basic conversion", function() {
    const EXPECTED_VALUE = "aba-foo";
    const actual = getKabobedName("Aba foo");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("Empty string", function() {
    const EXPECTED_VALUE = "";
    const actual = getKabobedName("");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("String with single quotes", function() {
    const EXPECTED_VALUE = "arbutus-_marina_";
    const actual = getKabobedName("Arbutus 'Marina'");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("null", function() {
    const EXPECTED_VALUE = "";
    const actual = getKabobedName(null);
    expect(actual).to.equal(EXPECTED_VALUE);
  });
});

describe("getUnKabobedName", function() {
  it("Basic conversion", function() {
    const EXPECTED_VALUE = "Aba foo";
    const actual = getUnKabobedName("aba-foo");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("Empty string", function() {
    const EXPECTED_VALUE = "";
    const actual = getUnKabobedName("");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("String with single quotes", function() {
    const EXPECTED_VALUE = "Arbutus 'marina'";
    const actual = getUnKabobedName("arbutus-_marina_");
    expect(actual).to.equal(EXPECTED_VALUE);
  });
  it("null", function() {
    const EXPECTED_VALUE = "";
    const actual = getUnKabobedName(null);
    expect(actual).to.equal(EXPECTED_VALUE);
  });
});

describe("HttpPicker", function() {
  it("http URL", function() {
    const http = { name: "http" };
    const https = { name: "https" };
    const httpPicker = new HttpPicker(http, https);
    const URL = "http://foo.com";
    const actual = httpPicker.gethttp(URL);
    expect(actual).to.equal(http);
  });
  it("https URL", function() {
    const http = { name: "http" };
    const https = { name: "https" };
    const httpPicker = new HttpPicker(http, https);
    const URL = "https://foo.com";
    const actual = httpPicker.gethttp(URL);
    expect(actual).to.equal(https);
  });
});
describe("LogObjects", function() {
  it("error one item", function() {
    const myLogger = new LogObjects();
    myLogger.error({ one: 1, two: 2 });
    expect(myLogger.toString()).to.equal("one,two\n1,2");
  });
  it("error two items", function() {
    const myLogger = new LogObjects();
    myLogger.error({ one: 1, two: 2 });
    myLogger.error({ one: 11, two: 12 });
    expect(myLogger.toString()).to.equal("one,two\n1,2\n11,12");
  });
  it("log one, error one item", function() {
    const myLogger = new LogObjects();
    myLogger.log({ one: 1, two: 2 });
    myLogger.error({ one: 11, two: 12 });
    expect(myLogger.toString()).to.equal("one,two\n11,12");
  });
  it("push no items", function() {
    const myLogger = new LogObjects();
    expect(myLogger.toString()).to.equal("");
  });
  it("log one, error one item with Level = log", function() {
    const myLogger = new LogObjects(1);
    myLogger.log({ one: 1, two: 2 });
    myLogger.error({ one: 11, two: 12 });
    expect(myLogger.toString()).to.equal("one,two\n1,2\n11,12");
  });

});
