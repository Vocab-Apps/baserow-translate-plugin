import { FieldType } from '@baserow/modules/database/fieldTypes'

import GridViewFieldText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldText'
import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import TranslationSubForm from '@baserow-translate-plugin/components/TranslationSubForm'
import ChatGPTSubForm from '@baserow-translate-plugin/components/ChatGPTSubForm'

import {
  genericContainsFilter,
  genericContainsWordFilter,
} from '@baserow/modules/database/utils/fieldFilters'

import RowCardFieldText from '@baserow/modules/database/components/card/RowCardFieldText'

export class TranslationFieldType extends FieldType {
  static getType() {
    return 'translation'
  }

  getIconClass() {
    return 'list-ol'
  }

  getName() {
    return 'Translation'
  }

  getFormComponent() {
    return TranslationSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldText
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }


  getCardComponent() {
    return RowCardFieldText
  }


  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
          ? stringA.localeCompare(stringB)
          : stringB.localeCompare(stringA)
    }
  }


  getContainsFilterFunction() {
    return genericContainsFilter
  }

  getContainsWordFilterFunction(field) {
    return genericContainsWordFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  getIsReadOnly() {
    return true
  }

  shouldFetchDataWhenAdded() {
    return true
  }



  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.text')
  }

  getDocsRequestExample(field) {
    return 'string'
  }  

}


export class ChatGPTFieldType extends FieldType {
  static getType() {
    return 'chatgpt'
  }

  getIconClass() {
    return 'list-ol'
  }

  getName() {
    return 'ChatGPT'
  }

  getFormComponent() {
    return ChatGPTSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldText
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }


  getCardComponent() {
    return RowCardFieldText
  }


  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
          ? stringA.localeCompare(stringB)
          : stringB.localeCompare(stringA)
    }
  }


  getContainsFilterFunction() {
    return genericContainsFilter
  }

  getContainsWordFilterFunction(field) {
    return genericContainsWordFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  getIsReadOnly() {
    return true
  }

  shouldFetchDataWhenAdded() {
    return true
  }



  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.text')
  }

  getDocsRequestExample(field) {
    return 'string'
  }  

}
