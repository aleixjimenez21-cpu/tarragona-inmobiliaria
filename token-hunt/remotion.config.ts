import { Config } from '@remotion/cli/config';
import fs from 'node:fs';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
Config.setCrf(16);
Config.setConcurrency(4);

// En este contenedor hay un Chromium que confía en el CA del proxy (necesario para
// descargar Google Fonts). Si no existe, Remotion usa/descarga su propio navegador.
const shell = process.env.REMOTION_CHROME ?? '/opt/pw-browsers/chromium';
if (fs.existsSync(shell)) {
  Config.setBrowserExecutable(shell);
}
