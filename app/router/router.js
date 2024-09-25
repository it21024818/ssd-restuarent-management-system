import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  routes: [
    
    {
      path: '/facebook-auth',
      name: 'facebook-auth',
      component: () => import('@/pages/Login.vue'),
      meta: {
        redirect: '/orders'
      }
    },
    {
        path: '/facebook-auth',
        beforeEnter(to, from, next) {
          // Handle the Facebook authentication code here
          const code = to.query.code;
          // ... handle the code ...
          next('/orders');
        }
      }
  ]
})