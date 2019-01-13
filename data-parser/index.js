const parse    = require('csv-parse/lib/sync')
const fs       = require('fs')
const got      = require('got')
const Parallel = require('async-parallel')

async function main() {
  const startTime = new Date().getTime()

  let trees = await getBaseData()
  console.log(`== Parsed initial data... (${new Date().getTime() - startTime} ms).`)

  let downloadStartTime = new Date().getTime()
  trees = await downloadImages(trees)
  console.log(`== Downloaded all images... (${new Date().getTime() - downloadStartTime} ms).`)

  fs.writeFileSync('data.js', formatAsJsFile(trees))

  console.log(`== Complete! (${new Date().getTime() - startTime} ms).`)
}

async function getBaseData() {
  const species  = toMap(parseCsv(readFile('species_names.csv')), 'botanical_name')
  const nativity = toMap(parseCsv(readFile('species_native_status_EOL_ID.csv')), 'botanical_name')
  const idk = await got('https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000')
  const treesRaw = parseCsv(idk.body)

  const trees = treesRaw.map(t => {
    const botanical = t['Name Botanical']
    return {
      'name_botanical': botanical,
      'name_common': t['Name Common'],
      'family_name_botanical': getOrDefault(species, botanical, 'family_botanical_name', 'Unknown'),
      'height_group': t['Height Group'],
      'latitude': t['Latitude'],
      'longitude': t['Longitude'],
      'nativity': getOrDefault(nativity, botanical, 'native', 'Unknown'),
      'eol_id': getOrDefault(nativity, botanical, 'EOL_ID', -1)
    }
  })

  return trees
}

async function downloadImages(trees) {
  let images = {}

  trees.filter(t => t.eol_id > 0)
       .forEach(t => images[t.eol_id] = '')

  let eolIds = Object.keys(images)

  await Parallel.each(eolIds, async (eolId) => {
    const index = eolIds.indexOf(eolId) + 1

    try {
      let result = await got(makeFetchUrl(eolId), { json: true })

      if (!result.body.taxonConcept.dataObjects) {
        return console.warn(`(${index}/${eolIds.length}) No image available for ${eolId}. Skipping.`)
      }

      let imgUrl    = result.body.taxonConcept.dataObjects[0].eolMediaURL
      let extension = imgUrl.substring(imgUrl.lastIndexOf('.') + 1)
      let filepath  = `img/${eolId}.${extension}`

      mkdir('img')

      await new Promise(resolve => {
        got.stream(imgUrl).pipe(fs.createWriteStream(filepath)).on('finish', resolve)
      })

      console.log(`(${index}/${eolIds.length}) Downloaded image for ${eolId}.`)

      images[eolId] = 'https://storage.googleapis.com/public-tree-map/img/' + filepath
    } catch (error) {
      console.warn(`(${index}/${eolIds.length}) Failed to fetch json for ${eolId}. Skipping.`)
    }
  }, 4)

  trees.forEach(t => t['images'] = images[t.eol_id] ? [images[t.eol_id]] : [])

  return trees
}

function mkdir(dirName) {
  fs.existsSync('img') || fs.mkdirSync('img')
}

function makeFetchUrl(eolId) {
  return `http://eol.org/api/pages/1.0.json?id=${eolId}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`
}

function formatAsJsFile(trees) {
  const prefix = 'app.setData('
  const body   = JSON.stringify(trees, null, 2)
  const suffix = ');'

  return prefix + body + suffix
}

function parseCsv(contents) {
  return parse(contents, { 
    columns: true,
    skip_empty_lines: true 
  })
}

function readFile(filename) {
  return fs.readFileSync(getPath(filename), 'utf8')
}

function getPath(filename) {
  return '../data/' + filename
}

function toMap(data, key) {
  const map = {}
  data.forEach(d => map[d[key]] = d)
  return map
}

function getOrDefault(map, key, field, defaultValue) {
  return map[key] && map[key][field] ? map[key][field] : defaultValue
}

main()
