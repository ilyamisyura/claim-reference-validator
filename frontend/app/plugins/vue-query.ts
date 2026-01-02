import { VueQueryPlugin, type VueQueryPluginOptions, QueryClient } from '@tanstack/vue-query'

export default defineNuxtPlugin((nuxtApp) => {
  const queryClient = new QueryClient()
  const options: VueQueryPluginOptions = {
    queryClient
  }
  nuxtApp.vueApp.use(VueQueryPlugin, options)
})

