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

export const actions = {
  facebookAuth({ commit }, code) {
    return new Promise((resolve, reject) => {
      axios.post('/facebook-auth', { code })
        .then(response => {
          const token = response.data.token;
          const username = response.data.username;
          commit('setAuthenticated', true);
          commit('setUsername', username);
          resolve();
        })
        .catch(error => {
          reject(error);
        });
    });
  },
};