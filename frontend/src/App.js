import Header from './Header.js';
import Fach from './Fach.js';
import Footer from './Footer.js';
import Gruppe from './Gruppe.js';
import Gruppen from './Gruppen.js';
import Lobby from './Lobby.js';
import Karte from './Karte.js';
import React from 'react';
import LoginBox from './LoginBox.js';
import {BrowserRouter as Router, Routes,Route } from "react-router-dom";
import SignIn from './LoginBox.js';



function App() {
    return(
     
      
      <Router>
        <Header/>
        <Routes>
          <Route path="/login" element={<SignIn/>}/>
          <Route path="/fach" element={<Fach/>}/>
          <Route path="/gruppe" element={<Gruppe/>}/>
          <Route path="/gruppen" element={<Gruppen/>}/>
          <Route path="/karte" element={<Karte/>}/>
          <Route path="/lobby" element={<Lobby/>}/>
          
        </Routes>
        <Footer/>
      </Router>
    
     
    );
}

export default App