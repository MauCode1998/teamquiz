import Header from './Header.js';
import Fach from './Fach.js';
import Footer from './Footer.js';
import Gruppe from './Gruppe.js';
import Gruppen from './Gruppen.js';
import Lobby from './Lobby.js';
import Game from './Game.js';
import React from 'react';
import LoginBox from './LoginBox.js';
import Register from './Register.js';
import {BrowserRouter as Router, Routes,Route, createBrowserRouter, RouterProvider } from "react-router-dom";
import { AuthProvider } from './AuthContext';
import ProtectedRoute from './components/ProtectedRoute';



function App() {
    return(
      <AuthProvider>
        <Router>
          <Header/>
          <Routes>
            <Route path="/" element={<LoginBox/>}/>
            <Route path="/register" element={<Register/>}/>
            <Route path="/groups" element={
              <ProtectedRoute>
                <Gruppen/>
              </ProtectedRoute>
            }/>
            <Route path="/groups/:groupName" element={
              <ProtectedRoute>
                <Gruppe/>
              </ProtectedRoute>
            }/>
            <Route path="/groups/:groupName/:subject" element={
              <ProtectedRoute>
                <Fach/>
              </ProtectedRoute>
            }/>
            <Route path="/lobby/:sessionId" element={
              <ProtectedRoute>
                <Lobby/>
              </ProtectedRoute>
            }/>
            <Route path="/game/:sessionId" element={
              <ProtectedRoute>
                <Game/>
              </ProtectedRoute>
            }/>
          </Routes>
          <Footer/>
        </Router>
      </AuthProvider>
    );
}

export default App