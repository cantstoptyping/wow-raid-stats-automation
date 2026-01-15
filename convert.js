const pptxgen = require("pptxgenjs");
const { html2pptx } = require("./html2pptx");

async function main() {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_16x9";
  
  // Add slides
  await html2pptx("slides/slide1.html", pptx);  // Title
  await html2pptx("slides/slide2.html", pptx);  // Overview
  await html2pptx("slides/slide3.html", pptx);  // Boss breakdown
  await html2pptx("slides/slide4.html", pptx);  // Top performers (DPS/HPS split)
  await html2pptx("slides/slide5.html", pptx);  // Top 5 DPS overall
  
  // Death causes slide (may not exist if no death data)
  const fs = require('fs');
  if (fs.existsSync("slides/slide6.html")) {
    await html2pptx("slides/slide6.html", pptx);  // Top 10 death causes
  }
  


  await html2pptx("slides/slide7.html", pptx);  // Closing
  
  // Save presentation
  const filename = `output/raid-stats-${Date.now()}.pptx`;
  await pptx.writeFile(filename);
  console.log(`Presentation created: ${filename}`);
}

main().catch(console.error);
