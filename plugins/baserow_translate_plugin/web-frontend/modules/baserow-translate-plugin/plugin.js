import {PluginNamePlugin} from '@baserow-translate-plugin/plugins'
import {TranslationFieldType} from '@baserow-translate-plugin/fieldtypes'
import {ChatGPTFieldType} from '@baserow-translate-plugin/fieldtypes'

export default (context) => {
  const { app } = context
  app.$registry.register('plugin', new PluginNamePlugin(context))
  app.$registry.register('field', new TranslationFieldType(context))
  app.$registry.register('field', new ChatGPTFieldType(context))
}
