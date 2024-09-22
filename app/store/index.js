export const state = () =>({
    authenticated: false
})

export const mutations = {
    storeId: (state, data)=>{
        state.id = data
    },
    setAuthenticated(state, authenticated) {
        state.authenticated = authenticated
    }
}
