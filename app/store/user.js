export const state = () =>({
    id:0,
    username:"",
    password:"",
    email:"",
})

export const mutations = {
    storeId: (state, data)=>{
        state.id = data
    },
    storeUsername: (state, data)=>{
        state.username = data
    },
    storePassword: (state, data)=>{
        state.password = data
    },
    storeEmail: (state, data)=>{
        state.email = data
    },
}
