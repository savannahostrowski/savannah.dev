param environmentName string
param location string = resourceGroup().location

param containerAppsEnvironmentName string = ''

var abbrs = loadJsonContent('../../abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = { 'azd-env-name': environmentName }

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2022-03-01' = {
  name: !empty(containerAppsEnvironmentName) ? containerAppsEnvironmentName : '${abbrs.appManagedEnvironments}${resourceToken}'
  location: location
  tags: tags
  properties: {
  }
}

output containerAppsEnvironmentName string = containerAppsEnvironment.name
