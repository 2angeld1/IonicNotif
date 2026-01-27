import { IonApp, IonRouterOutlet } from '@ionic/react';
import { IonReactRouter } from '@ionic/react-router';
import { Route, Redirect } from 'react-router-dom';
import HomePage from './pages/HomePage';
import { VoiceModeProvider } from './contexts/VoiceModeContext';
import { ConvoyProvider } from './contexts/ConvoyContext';

function App() {
  return (
    <VoiceModeProvider>
      <ConvoyProvider>
        <IonApp>
          <IonReactRouter>
            <IonRouterOutlet>
              <Route exact path="/home" component={HomePage} />
              <Route exact path="/">
                <Redirect to="/home" />
              </Route>
            </IonRouterOutlet>
          </IonReactRouter>
        </IonApp>
      </ConvoyProvider>
    </VoiceModeProvider>
  );
}

export default App;
