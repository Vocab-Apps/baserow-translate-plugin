<template>
  <div>

    <div class="control">
      <label class="control__label control__label--small">
          Select Source Field
      </label>
      <Dropdown
        v-model="values.source_field_id"
        @input="sourceFieldSelected"
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

  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'


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
    async sourceFieldSelected() {
      console.log('source_field_id: ', this.values.source_field_id);
      const selectedField = this.$store.getters['field/get'](
          this.values.source_field_id
      );
      // console.log('selectedField: ', selectedField);
      this.selectedSourceFieldLanguage = selectedField.language;
      console.log('selectedSourceFieldLanguage: ', this.selectedSourceFieldLanguage);
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

      console.log('allFields: ', allFields);

      return allFields;
    },
  }  
}
</script>
