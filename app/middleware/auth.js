export default function ({ store, redirect, route }) {
  const publicRoutes = ['/Login', '/Signup', '/'];

  if (!store.state.authenticated && !publicRoutes.includes(route.path)) {
    return redirect('/')
  }
}