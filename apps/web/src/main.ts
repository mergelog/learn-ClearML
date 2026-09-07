import {enableProdMode} from '@angular/core';
import {bootstrapApplication} from '@angular/platform-browser';
import {ConfigurationService, fetchConfigOutSideAngular} from '@common/shared/services/configuration.service';
import {updateHttpUrlBaseConstant} from '~/app.constants';
import {Environment} from './environments/base';
import {AppRootComponent} from '~/app';
import {getAppConfig} from '~/app.config';
import webEnvironment from '../.env';

const readEnvironmentVariable = (source: string, name: string): string | undefined => {
  const prefix = `${name}=`;
  const line = source
    .split(/\r?\n/)
    .map(value => value.trim())
    .find(value => value.startsWith(prefix));

  if (!line) {
    return undefined;
  }

  const value = line.slice(prefix.length).trim();
  const isQuoted =
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"));

  return isQuoted ? value.slice(1, -1) : value;
};

const environment = ConfigurationService.globalEnvironment;
const primeUiLicense = readEnvironmentVariable(webEnvironment, 'PRIMEUI_LICENSE');

if (environment.production) {
  enableProdMode();
}

(async () => {
  let configData = {} as Environment;
  try {
    configData = await fetchConfigOutSideAngular();
    (window as any).configuration = configData;
  } finally {
    const baseHref = (window as any).__env?.subPath || '' as string;
    updateHttpUrlBaseConstant({...environment, ...configData, ...(baseHref && !baseHref.startsWith('${') && {apiBaseUrl: baseHref + environment.apiBaseUrl})});
    bootstrapApplication(AppRootComponent, getAppConfig(configData, primeUiLicense)).catch(err => console.error(err));
  }
})();
