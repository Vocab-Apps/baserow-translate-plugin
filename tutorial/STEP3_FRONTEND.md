# Frontend / GUI Changes

We finished the backend changes, but we can't yet use our two new fields, because we need to make some GUI changes first. 

## Create views
### TranslationSubForm
We need to create some GUI components for the two new field types. Those are VueJS / Nuxt components. I'm not an expert in frontend code, I just pretty much randomy try stuff until it works. Open this file:
`plugins/translate_plugin/web-frontend/modules/translate-plugin/components/TranslationSubForm.vue`

I won't paste the full source here (refer to the sample code), but i'll comment a few snippets. Over here, we add a dropdown to select the *source* field. That's the field which contains the text to translate. The available fields need to be in a member variable called `tableFields`, which is a *computed property* in the VueJS component.
```
    <div class="control">
      <label class="control__label control__label--small">
          Select Source Field
      </label>
      <Dropdown
        v-model="values.source_field_id"
      >
        <DropdownItem
          v-for="field in tableFields"
          :key="field.id"
          :name="field.name"
          :value="field.id"
          :icon="field.icon"
        ></DropdownItem>
      </Dropdown>
     </div>
```
These two are very simple: we just ask the user to type in the *source* and *target* language (like `fr` and `en`):
```
    <div class="control">
      <label class="control__label control__label--small">
          Type in language to translate from
      </label>      
      <div class="control__elements">
              <input
                v-model="values.source_language"
                class="input"
                type="text"
              />
    </div>
   </div>

    <div class="control">
      <label class="control__label control__label--small">
          Type in language to translate to
      </label>      
      <div class="control__elements">
              <input
                v-model="values.target_language"
                class="input"
                type="text"
              />
     </div>
    </div>
```

Now, here's the code and state for the component. It specifies which values we'll be storing, and adds a *computed property* which tells the component what the different fileds available in the table are (so that the user can select a source field).
```
export default {
  name: 'TranslationSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['source_field_id', 'source_language', 'target_language'],
      values: {
        source_field_id: '',
        source_language: '',
        target_language: ''
      }
    }
  },
  methods: {
    isFormValid() {
      return true
    },
  },
  computed: {
    tableFields() {
      console.log("computed: tableFields");
      // collect all fields, including primary field in this table
      const primaryField = this.$store.getters['field/getPrimary'];
      const fields = this.$store.getters['field/getAll']

      let allFields = [primaryField];
      allFields = allFields.concat(fields);
      
      // remove any undefined field
      allFields = allFields.filter((f) => {
              return f != undefined
      });

      console.log('allFields: ', allFields);

      return allFields;
    },
  }  
}
```

### ChatGPTSubForm
the ChatGPT GUI component is much simpler. Its code will be in `plugins/translate_plugin/web-frontend/modules/translate-plugin/components/ChatGPTSubForm.vue`. It just contains the ChatGPT prompt, so it's easy to implement:
```
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
```