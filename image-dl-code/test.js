// some basic Unit Tests:
// $ npm run test
const chai = require("chai");
const expect = chai.expect;
const should = chai.should;

const {
  getMediaURL,
  getKabobedName,
  getUnKabobedName,
  HttpPicker
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
