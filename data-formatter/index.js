const sqlite = require('sqlite3').verbose()
const db     = new sqlite.Database('./database.sqlite3')
const fs     = require('fs')

if (process.argv.length != 3) {
  console.error('No output file provided.')
  process.exit()
}

const outputFile = process.argv[2]

const query = `SELECT trees.name_botanical, 
                    trees.name_common,
                    trees.latitude,
                    trees.longitude,
                    trees.address,
                    trees.street,
                    trees.on_address,
                    trees.on_street,
                    trees.location_description,
                    species.native,
                    species.eol_image,
                    species.family_botanical_name
             FROM trees, species
             WHERE trees.species_id = species.id`

db.all(query, [], (err, rows) => {
  if (err) {
    console.error(err)
  }

  let prefix = 'app.setData('
  let body   = JSON.stringify(rows, null, 2)
  let suffix = ');'

  fs.writeFileSync(outputFile, prefix + body + suffix)

  console.log('Complete!');
})

db.close()
