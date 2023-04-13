import {PluginNamePlugin} from '@baserow-translate-plugin/plugins'

export default (context) => {
  const { app } = context
  app.$registry.register('plugin', new PluginNamePlugin(context))
}
