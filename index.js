const parse    = require('csv-parse/lib/sync')
const fs       = require('fs')
const got      = require('got')
const Parallel = require('async-parallel')
const sharp    = require('sharp')

const DEBUG = !process.env.CI

async function main() {
  mkdir('build')
  mkdir('tmp')

  log('Starting...')

  const startTime = new Date().getTime()

  let trees = await getBaseData()
  log(`== Parsed initial data... (${new Date().getTime() - startTime} ms)`)

  let downloadStartTime = new Date().getTime()
  trees = await downloadImages(trees)
  log(`== Downloaded all images... (${new Date().getTime() - downloadStartTime} ms)`)

  mkdir('build/data')
  fs.writeFileSync('build/data/trees.json', JSON.stringify(trees, null, 2))

  log(`== Complete! (${new Date().getTime() - startTime} ms)`)
}

async function getBaseData() {
  const species  = toMap(parseCsv(readFile('data/species_names.csv')), 'botanical_name')
  const nativity = toMap(parseCsv(readFile('data/species_native_status_EOL_ID.csv')), 'botanical_name')
  const treesRaw = parseCsv((await got('https://data.smgov.net/resource/w8ue-6cnd.csv?$limit=50000')).body)

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
        return log(`(${index}/${eolIds.length}) No image available for ${eolId}. Skipping.`)
      }

      let imgUrl    = result.body.taxonConcept.dataObjects[0].eolMediaURL
      let extension = imgUrl.substring(imgUrl.lastIndexOf('.') + 1)
      let filename  = `${eolId}.${extension}`
      let filepath  = `build/img/${filename}`

      mkdir('build/img')

      await new Promise(resolve => {
        got.stream(imgUrl).pipe(fs.createWriteStream(filepath)).on('finish', resolve)
      })

      let resizedData = await sharp(filepath).resize(1024, 1024, { fit: 'inside' })
                                             .toBuffer()
      fs.writeFileSync(filepath, resizedData)
      
      log(`(${index}/${eolIds.length}) Downloaded image for ${eolId}.`)

      images[eolId] = 'https://storage.googleapis.com/public-tree-map/img/' + filename 
    } catch (error) {
      log(`(${index}/${eolIds.length}) Failed to fetch json for ${eolId}. Skipping.`)
    }
  }, 4)

  trees.forEach(t => t['images'] = images[t.eol_id] ? [images[t.eol_id]] : [])

  return trees
}

function mkdir(dirname) {
  fs.existsSync(dirname) || fs.mkdirSync(dirname)
}

function makeFetchUrl(eolId) {
  return `http://eol.org/api/pages/1.0.json?id=${eolId}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`
}

function parseCsv(contents) {
  return parse(contents, { 
    columns: true,
    skip_empty_lines: true 
  })
}

function readFile(filepath) {
  return fs.readFileSync(filepath, 'utf8')
}

function toMap(data, key) {
  const map = {}
  data.forEach(d => map[d[key]] = d)
  return map
}

function getOrDefault(map, key, field, defaultValue) {
  return map[key] && map[key][field] ? map[key][field] : defaultValue
}

function log(message) {
  if (DEBUG) {
    console.log(message)
  } else {
    fs.appendFileSync('tmp/log.txt', message + '\n')
  }
}

main()
