<template>
  <div>

    <div class="control">
      <label class="control__label control__label--small">
          Type in prompt for ChatGPT, you may reference other fields such as {Field 1}
      </label>      
      <div class="control__elements">
              <input
                v-model="values.prompt"
                class="input"
                type="text"
              />
    </div>
   </div>

  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'


export default {
  name: 'ChatGPTSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['prompt'],
      values: {
        prompt: ''
      }
    }
  },
  methods: {
    isFormValid() {
      return true
    },
  }  
}
</script>
