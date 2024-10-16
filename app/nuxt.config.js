import colors from "vuetify/es5/util/colors";

export default {
  buildModules: ["@nuxtjs/vuetify"],
  modules: [
    "@nuxtjs/axios",
    // https://go.nuxtjs.dev/pwa
    // '@nuxtjs/pwa',
    // https://go.nuxtjs.dev/content
    "@nuxt/content",
    "vue-sweetalert2/nuxt/no-css",
    "nuxt-webfontloader",
    "@nuxtjs/dotenv",
  ],
  components: true,

  router: {
    middleware: ["auth"],
  },

  // Disable server-side rendering: https://go.nuxtjs.dev/ssr-mode
  ssr: true,

  // Target: https://go.nuxtjs.dev/config-target
  target: "static",

  // Global page headers: https://go.nuxtjs.dev/config-head
  head: {
    title: "Cafe Green",
    meta: [
      { charset: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { hid: "description", name: "description", content: "eCommerce Website" },
      { name: "format-detection", content: "telephone=no" },
    ],
    link: [{ rel: "icon", type: "image/x-icon", href: "/logo.jpg" }],
    script: [
      {
        src: 'https://accounts.google.com/gsi/client',
        async: true,
        defer: true,
      },
    ],
  },

  // Global CSS: https://go.nuxtjs.dev/config-css
  css: ["@sweetalert2/theme-material-ui", "~/assets/main.css"],

  // Plugins to run before rendering page: https://go.nuxtjs.dev/config-plugins
  // plugins: ["~/plugins/googleAuth.js"],

  webfontloader: {
    google: {
      families: ["DM+Sans:wght@400;500;700&display=swap"],
    },
  },

  //PWA module configuration: https://go.nuxtjs.dev/pwa
  //   pwa: {
  //     manifest: {
  //       lang: 'en'
  //     }
  //   },

  // Content module configuration: https://go.nuxtjs.dev/config-content
  content: {},

  // Vuetify module configuration: https://go.nuxtjs.dev/config-vuetify
  vuetify: {
    customVariables: ["~/assets/variables.scss"],
    defaultAssets: {
      font: {
        family: "DM Sans",
        size: 15,
      },
    },
    treeShake: true,
    theme: {
      light: true,
      themes: {
        light: {
          primary: colors.deepPurple.darken1,
          bg: "#ffffff",
          surface: "#ffffff",
          accent: colors.grey.darken3,
          secondary: colors.amber.darken3,
          info: colors.teal.lighten1,
          warning: colors.amber.base,
          error: colors.deepOrange.accent4,
          success: colors.green.accent3,
        },
        dark: {
          primary: colors.deepPurple.darken1,
          bg: "#0a0514",
          surface: "#130a24",
          accent: colors.grey.darken3,
          secondary: colors.amber.darken3,
          info: colors.teal.lighten1,
          warning: colors.amber.base,
          error: colors.deepOrange.accent4,
          success: colors.green.accent3,
        },
      },
    },
  },

  // Build Configuration: https://go.nuxtjs.dev/config-build
  build: {},

  render: {
    http: {
      headers: {
        'Content-Security-Policy': "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; object-src 'none'",
        'X-Content-Type-Options': 'nosniff',
      },
    },
  },
};
