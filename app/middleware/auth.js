export default function ({ store, redirect, route }) {
  const publicRoutes = ['/Login', '/Signup', '/', '/google-auth', '/facebook-auth'];

  if (!store.state.authenticated && !publicRoutes.includes(route.path)) {
    return redirect('/')
  }
}