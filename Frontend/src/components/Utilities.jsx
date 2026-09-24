export const initialFormState = {
  theme:  '',
  supervisor: '',
  qualification: '',
  tags:''
};

export const uploadKey = {
  visitor_id: '',
  vkr_id: '',
}

export const checkKey = {
  visitor_id: '',
};

export const uploadHeaders = {
  API_Key: ''
}

export const uploadForm = {
  supervisor: '',
};

export const stylesShared = {
  label:{
      color:'#ffffff',
  }
};

export const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};

export const tailLayout = {
  wrapperCol: { offset: 6, span: 12 },
};

export const onChange_filter = (num) => {
    let number = num.toString()
    if (number.length >= 2) {
      if ((['0', '5', '6', '7', '8', '9'].includes(number.slice(-1))) || (['11', '12', '13', '14'].includes(number.slice(-2)))) {
        return 'работ'
      }
      else if ((['2', '3', '4'].includes(number.slice(-1))) && !(['11', '12', '13', '14'].includes(number.slice(-2)))) {
        return 'работы'
      }
      else if ((['1'].includes(number.slice(-1))) && !(['11'].includes(number.slice(-2)))) {
        return 'работу'
      }
    }
    else if ((number.length === 1))
      if (['1'].includes(number)) {
        return 'работу'
      }
      else if (['2', '3', '4'].includes(number)) {
        return 'работы'
      }
      else if (['0', '5', '6', '7', '8', '9'].includes(number)) {
        return 'работ'
      }
    }

export const noteGet = () => {
  return (
    <div className="w-120 text-justify text-black">
        <h2 className='text-center font-semibold text-lg'>Памятка</h2>
        <ul id="note-list" className='list-disc'>
          <li className='my-2'>Поиск по названию ВКР осуществляется как на полном названии ВКР, так и на основе ключевого слова из названия; можно вводить ключевые слова в следующем формате: Ключевое слово1, Ключевое слово2</li>
          <li className='my-2'>В поле "Квалификация" можно выбрать одно из значений: Бакалавриат или Магистратура</li>
          <li className='my-2'>В поле "Научный руководитель" можно выбрать несколько научных руководителей</li>
          <li className='my-2'>Тэги помогают с поиском ВКР, если отсутствуют ключевые слова (например, при вводе тэга "Грузоперевозки" программа выведет "Адаптивная модель грузоперевозок"); можно выбрать несколько тэгов</li>
          <li className='my-2'>ВАЖНО! Если тэг отсутствует в предложенном списке, то его можно ввести в поле "Тэги". В данном случае будут показаны работы с наиболее близкими по тематике тэгами</li>
        </ul>
      </div>
  )
}

export const noteUpload = () => {
  return (
     <div className="w-130 text-justify text-white">
        <h2 className='text-center font-semibold text-lg'>Памятка</h2>
        <ul id="note-list" className='list-disc'>
          <li className='my-2'>В поле "Научный руководитель" можно выбрать только одного руководителя; если руководителя нет в списке, то необходимо поставить 'галочку' в окне 'Руководителя нет в списке' и заполнить его данные: Фамилия Имя Отчество, место работы и учёная степень</li>
          {/* <li className='my-2'>Принимаются файлы только в формате .pdf; название файла должно быть на английском языке и соответствовать следующему шаблону: год выпуска_VKR_группа_фамилия.pdf (например, 2023_VKR_B19_803_Ivanov.pdf)</li>    */}
        </ul>
      </div>
  )
};

